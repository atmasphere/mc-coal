import logging
import mimetypes
import urlparse

from google.appengine.api import images, memcache, urlfetch
from google.appengine.api.images import NotImageError
from google.appengine.ext import ndb, blobstore
from google.appengine.ext.webapp import blobstore_handlers

from poster.encode import multipart_encode, MultipartParam

from webapp2_extras.routes import RedirectRoute


IMAGE_HEADER_SIZE = 50000
IMAGE_UPLOAD_URL = '/_bscs/data'


class NdbImage(ndb.Model):
    """
    An NDB model class that helps create and work with images stored in the `Blobstore`_.
    Please note that you should never call the constructor for this class directly when creating an image.
    Instead, use the :py:meth:`create` method.
    """
    #: The `BlobKey`_ entity for the image's `Blobstore`_ value.
    blob_key = ndb.BlobKeyProperty(required=False)
    #: The original URL that the image data was fetched from, if applicable.
    source_url = ndb.StringProperty(required=False, default=None)
    #: The create timestamp.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: The last modified timestamp.
    modified = ndb.DateTimeProperty(auto_now=True)

    @property
    def key_as_string(self):
        return self.key.urlsafe()

    @property
    def blob_info(self):
        if self.blob_key is not None:
            return blobstore.BlobInfo.get(self.blob_key)
        return None

    @blob_info.setter
    def blob_info(self, blob_info):
        self.blob_key = blob_info.key()

    @property
    def image(self):
        """
        The Google `Image`_ entity for the image.
        """
        if self.blob_key is not None:
            return images.Image(blob_key=self.blob_key)
        return None

    @property
    def format(self):
        """
        The format of the image (see `Image.format`_ for possible values).
        If there is no image data, this will be ``None``.
        """
        if self.image is not None:
            try:
                return self.image.format
            except NotImageError:
                data = self.fetch_data(0, IMAGE_HEADER_SIZE)
                img = images.Image(image_data=data)
                return img.format
        return None

    @property
    def width(self):
        """
        The width of the image in pixels (see `Image.width`_ for more documentation).
        If there is no image data, this will be ``None``.
        """
        if self.image is not None:
            try:
                return self.image.width
            except NotImageError:
                data = self.fetch_data(0, IMAGE_HEADER_SIZE)
                img = images.Image(image_data=data)
                return img.width
        return None

    @property
    def height(self):
        """
        The height of the image in pixels (see `Image.height`_ for more documentation).
        If there is no image data, this will be ``None``.
        """
        if self.image is not None:
            try:
                return self.image.height
            except NotImageError:
                data = self.fetch_data(0, IMAGE_HEADER_SIZE)
                img = images.Image(image_data=data)
                return img.height
        return None

    @property
    def image_data(self):
        """
        The raw image data as returned by a `BlobReader`_.
        If there is no image data, this will be ``None``.
        """
        if self.blob_key is not None:
            return blobstore.BlobReader(self.blob_key).read()
        return None

    def get_serving_url(self, size=None, crop=False, secure_url=None):
        """
        Returns the serving URL for the image. It works just like the `Image.get_serving_url`_ function,
        but adds caching. The cache timeout is controlled by the :py:attr:`.SERVING_URL_TIMEOUT` setting.

        :param size: An integer supplying the size of resulting images.
            See `Image.get_serving_url`_ for more detailed argument information.
        :param crop: Specify ``true`` for a cropped image, and ``false`` for a re-sized image.
            See `Image.get_serving_url`_ for more detailed argument information.
        :param secure_url: Specify ``true`` for a https url.
            See `Image.get_serving_url`_ for more detailed argument information.
        :return: The serving URL for the image (see `Image.get_serving_url`_ for more detailed information).
        """
        serving_url = None
        if self.blob_key is not None:
            namespace = "image-serving-url"
            key = "%s-%s-%s" % (self.key, size, crop)
            serving_url = memcache.get(key, namespace=namespace)
            if serving_url is None:
                tries = 0
                while tries < 3:
                    try:
                        tries += 1
                        serving_url = images.get_serving_url(str(self.blob_key), size=size, crop=crop, secure_url=secure_url)
                        if serving_url is not None:
                            break
                    except Exception, e:
                        if tries >= 3:
                            logging.error("Unable to get image serving URL: %s" % e)
                if serving_url is not None:
                    memcache.set(key, serving_url, time=3600, namespace=namespace)
        return serving_url

    def put_data(self, data, filename=None, mime_type=None):
        previous_blob_info = self.blob_info
        filename = filename or self.key_as_string
        mime_type = mime_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        url = blobstore.create_upload_url('/_bscs/data')
        params = []
        params.append(MultipartParam("file", filename=filename, filetype=mime_type, value=data))
        payload_generator, headers = multipart_encode(params)
        payload = str().join(payload_generator)
        key = None
        try:
            result = urlfetch.fetch(url=url, payload=payload, method=urlfetch.POST, headers=headers, deadline=10, follow_redirects=False)
            if "location" in result.headers:
                location = result.headers["location"]
                key = location[location.rfind("/") + 1:]
                if key:
                    self.blob_key = ndb.BlobKey(key)
                    self.put()
                    if previous_blob_info is not None:
                        previous_blob_info.delete()
                return self.blob_key
            else:
                return None
        except Exception as e:
            logging.error(e)
            if key is not None:
                blob_info = blobstore.get(key)
                if blob_info is not None:
                    blob_info.delete()
            return None

    def fetch_data(self, *args, **kwargs):
        return blobstore.fetch_data(self.blob_key, *args, **kwargs)

    @classmethod
    def _pre_delete_hook(cls, key):
        image = key.get()
        if image.blob_info is not None:
            image.blob_info.delete()

    @classmethod
    def create_new_entity(cls, **kwargs):
        """
        Called to create a new entity. The default implementation simply creates the entity with the default constructor
        and calls ``put()``. This method allows the class to be mixed-in with :py:class:`agar.models.NamedModel`.

        :param kwargs: Parameters to be passed to the constructor.
        """
        image = cls(**kwargs)
        image.put()
        return image

    @classmethod
    def create(cls, blob_key=None, blob_info=None, data=None, filename=None, url=None, mime_type=None, **kwargs):
        """
        Create an ``Image``. Use this class method rather than creating an image with the constructor. You must provide one
        of the following parameters ``blob_info``, ``data``, or ``url`` to specify the image data to use.

        :param blob_key: The `Blobstore`_ data to use as the image data. If this parameter is not ``None``, all
            other parameters will be ignored as they are not needed (Only use with `NdbImage`).
        :param blob_info: The `Blobstore`_ data to use as the image data. If this parameter is not ``None``, all
            other parameters will be ignored as they are not needed (Do not use with `NdbImage`).
        :param data: The image data that should be put in the `Blobstore`_ and used as the image data.
        :param filename: The filename of the image data. If not provided, the filename will be guessed from the URL
            or, if there is no URL, it will be set to the stringified `Key`_ of the image entity.
        :param url: The URL to fetch the image data from and then place in the `Blobstore`_ to be used as the image data.
        :param mime_type: The `mime type`_ to use for the `Blobstore`_ image data.
            If ``None``, it will attempt to guess the mime type from the url fetch response headers or the filename.
        :param parent:  Inherited from `Model`_. The `Model`_ instance or `Key`_ instance for the entity that is the new
            image's parent.
        :param key_name: Inherited from `Model`_. The name for the new entity. The name becomes part of the primary key.
        :param key: Inherited from `Model`_. The explicit `Key`_ instance for the new entity.
            Cannot be used with ``key_name`` or ``parent``. If ``None``, falls back on the behavior for ``key_name`` and
            ``parent``.
        :param kwargs: Initial values for the instance's properties, as keyword arguments.  Useful if subclassing.
        :return: An instance of the ``NdbImage`` class.
        """
        if filename is not None:
            filename = filename.encode('ascii', 'ignore')
        if url is not None:
            url = url.encode('ascii', 'ignore')
        if blob_info is not None:
            kwargs['blob_key'] = blob_info.key()
            return cls.create_new_entity(**kwargs)
        if blob_key is not None:
            kwargs['blob_key'] = blob_key
            return cls.create_new_entity(**kwargs)
        if data is None:
            if url is not None:
                response = urlfetch.fetch(url)
                data = response.content
                mime_type = mime_type or response.headers.get('Content-Type', None)
                if filename is None:
                    path = urlparse.urlsplit(url)[2]
                    filename = path[path.rfind('/')+1:]
        if data is None:
            raise images.BadImageError("No image data")
        image = cls.create_new_entity(source_url=url, **kwargs)
        filename = filename or image.key_as_string
        mime_type = mime_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        if mime_type not in ['image/jpeg', 'image/png', 'image/gif']:
            message = "The image mime type (%s) isn't valid" % mime_type
            logging.warning(message)
            image.key.delete()
            raise images.BadImageError(message)
        gae_image = images.Image(data)
        format = gae_image.format
        new_format = None
        if mime_type == 'image/jpeg' and format != images.JPEG:
            new_format = images.JPEG
        if mime_type == 'image/png' and format != images.PNG:
            new_format = images.PNG
        if new_format is not None:
            data = images.crop(data, 0.0, 0.0, 1.0, 1.0, output_encoding=new_format, quality=100)
        image.put_data(data, mime_type=mime_type)
        return image.key.get()


class BlobstoreDataHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        files = self.get_uploads('file')
        if files:
            blob_info = files[0]
            self.redirect('{0}'.format(blob_info.key()))
        else:
            self.abort(400, "No files in POST")


routes = [
    RedirectRoute(IMAGE_UPLOAD_URL, handler=BlobstoreDataHandler, name="image_put_data"),
]
