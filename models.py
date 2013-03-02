from google.appengine.ext import ndb
from google.appengine.api import users

import webapp2_extras.appengine.auth.models as auth_models


class User(auth_models.User):
    active = ndb.BooleanProperty(default=False)
    admin = ndb.BooleanProperty(default=False)
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    username = ndb.StringProperty()

    @classmethod
    def get_gae_user_auth_id(cls, gae_user_id=None, gae_user=None):
        if not gae_user_id:
            gae_user_id = gae_user.user_id() if gae_user else 'ANON'
        return 'gaeuser:{0}'.format(gae_user_id)

    @classmethod
    def get_by_gae_user(cls, gae_user_id=None, gae_user=None):
        return cls.get_by_auth_id(cls.get_gae_user_auth_id(gae_user_id=gae_user_id, gae_user=gae_user))

    @classmethod
    def create_by_gae_user(cls, gae_user=None):
        if not gae_user:
            gae_user = users.get_current_user()
        if gae_user:
            return cls.create_user(
                cls.get_gae_user_auth_id(gae_user=gae_user),
                email=gae_user.email(),
                nickname=gae_user.nickname()
            )
        return False, None

    @classmethod
    def lookup(cls, email):
        return cls.query().filter(ndb.StringProperty('email') == email).get()
