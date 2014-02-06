import logging

from google.appengine.ext import ndb

import webapp2
from webapp2_extras.routes import RedirectRoute

from wtforms import form, fields, validators

from forms import StringListField, AtLeastOneAdmin, UniqueUsernames
from forms import UniquePort, UniqueVersion, VersionUrlExists
import gce
from models import Server, User, MinecraftDownload
from server_handler import ServerHandlerBase, PagingHandler
from user_auth import ON_SERVER, UserHandler, authentication_required, authenticate, authenticate_admin


RESULTS_PER_PAGE = 50


class AdminHandlerBase(ServerHandlerBase):
    pass


class AdminPagingHandler(AdminHandlerBase, PagingHandler):
    pass


class AdminHandler(AdminPagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_all(), User.query_all_reverse(), RESULTS_PER_PAGE
        )
        servers = []
        for server in Server.query():
            servers.append(server)
        instance = gce.Instance.singleton()
        status = instance.status()
        context = {'servers': servers, 'instance': instance, 'status': status}
        self.render_template('admin.html', context=context)


class UserForm(form.Form):
    active = fields.BooleanField(u'Active', [validators.Optional()])
    admin = fields.BooleanField(u'Admin', [AtLeastOneAdmin()])
    usernames = StringListField(u'Usernames', validators=[validators.Optional(), UniqueUsernames()])

    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user


class UsersHandler(AdminPagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_all(), User.query_all_reverse(), RESULTS_PER_PAGE
        )
        context = {'users': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('users.html', context=context)


class UserEditHandler(AdminHandlerBase):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            form = UserForm(user=user, obj=user)
        except Exception, e:
            logging.error(u"Error GETting user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            form = UserForm(user=user, formdata=self.request.POST, obj=user)
            if form.validate():
                user.active = form.active.data
                user.admin = form.admin.data
                user.set_usernames(form.usernames.data)
                user.put()
                self.redirect(webapp2.uri_for('users'))
        except Exception, e:
            logging.error(u"Error POSTing user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)


class UserRemoveHandler(AdminHandlerBase):
    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            if user.admin:
                self.abort(405)  # Method Not Allowed
            user.key.delete()
        except Exception, e:
            logging.error(u"Error removing user: {0}".format(e))
        self.redirect(webapp2.uri_for('users'))


class ServerForm(form.Form):
    name = fields.StringField(u'Name', [validators.Required()])


class ServerCreateHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        form = ServerForm()
        context = {'form': form}
        self.render_template('server_create.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        try:
            form = ServerForm(formdata=self.request.POST)
            if form.validate():
                server = Server.create(name=form.name.data, is_gce=False)
                self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))
        except Exception, e:
            logging.error(u"Error POSTing server: {0}".format(e))
            self.abort(404)
        context = {'form': form}
        self.render_template('server_create.html', context=context)


class ServerEditHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            if server.is_gce:
                self.redirect(webapp2.uri_for('server_gce', key=server.key.urlsafe()))
            form = ServerForm(obj=server)
        except Exception, e:
            logging.error(u"Error GETting server: {0}".format(e))
            self.abort(404)
        context = {'edit_server': server, 'form': form, 'action': webapp2.uri_for('server', key=server.key.urlsafe())}
        self.render_template('server.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            form = ServerForm(formdata=self.request.POST)
            if form.validate():
                server.name = form.name.data
                server.put()
                self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))
        except Exception, e:
            logging.error(u"Error POSTing server: {0}".format(e))
            self.abort(404)
        context = {'edit_server': server, 'form': form, 'action': webapp2.uri_for('server', key=server.key.urlsafe())}
        self.render_template('server.html', context=context)


class ServerPropertiesForm(ServerForm):
    server_port = fields.IntegerField(
        u'The minecraft server port to use (leave blank for first available)',
        validators=[validators.Optional(), validators.NumberRange(min=25565, max=25575), UniquePort()]
    )
    version = fields.SelectField(u'Minecraft Version', validators=[validators.DataRequired()])
    memory = fields.SelectField(u'Server memory', validators=[validators.DataRequired()], default='256M')
    operator = fields.StringField(u'Initial operator username', default='')
    idle_timeout = fields.IntegerField(
        u'Number of minutes before an idle server is automatically paused (zero means never)',
        validators=[validators.InputRequired(), validators.NumberRange(min=0, max=60)],
        default=5
    )
    motd = fields.StringField(u'Message of the day', default='An MC-COAL Minecraft Server')
    white_list = fields.BooleanField(u'Enable whitelist', default=False)
    gamemode = fields.SelectField(u'Game mode', default='0')
    force_gamemode = fields.BooleanField(u'Force players to join in the default game mode', default=False)
    level_type = fields.SelectField(u'Type of map', default='DEFAULT')
    level_seed = fields.StringField(u'Seed for the world', default='')
    generator_settings = fields.StringField(u'Settings used to customize Superflat world generation', default='')
    difficulty = fields.SelectField(u'Server difficulty', default='1')
    pvp = fields.BooleanField(u'Enable PvP', default=False)
    hardcore = fields.BooleanField(u'Hardcore mode (players will be permanently banned if they die)', default=False)
    allow_flight = fields.BooleanField(u'Allow users to use flight while in Survival mode', default=False)
    allow_nether = fields.BooleanField(u'Allow players to travel to the Nether', default=True)
    max_build_height = fields.IntegerField(
        u'Maximum height in which building is allowed',
        validators=[validators.NumberRange(min=0, max=1024)],
        default=256
    )
    generate_structures = fields.BooleanField(u'Generate structures', default=True)
    spawn_npcs = fields.BooleanField(u'Spawn villagers', default=True)
    spawn_animals = fields.BooleanField(u'Spawn animals', default=True)
    spawn_monsters = fields.BooleanField(u'Spawn monsters', default=True)
    player_idle_timeout = fields.IntegerField(
        u'Number of minutes before an idle player is kicked (zero means never)',
        validators=[validators.NumberRange(min=0, max=60)],
        default=0
    )
    spawn_protection = fields.IntegerField(
        u'Radius of spawn area protection',
        validators=[validators.NumberRange(min=0, max=64)],
        default=16
    )
    enable_command_block = fields.BooleanField(u'Enable command blocks', default=False)
    snooper_enabled = fields.BooleanField(
        u'Send snoop data regularly to snoop.minecraft.net', default=True
    )
    resource_pack = fields.StringField(
        u'Prompt clients to download resource pack from this URL', default=''
    )
    op_permission_level = fields.SelectField(u'Ops permission level', default='3')

    def __init__(self, server=None, *args, **kwargs):
        super(ServerPropertiesForm, self).__init__(*args, **kwargs)
        self.server = server
        self.version.choices = [
            (d.version, d.version) for d in MinecraftDownload.query().fetch(100)
        ]
        self.memory.choices = [
            ('256M', '256 Megabytes'),
            ('512M', '512 Megabytes'),
            ('1G', '1 Gigabyte')
        ]
        self.gamemode.choices = [
            ('0', 'Survival'),
            ('1', 'Creative'),
            ('2', 'Adventure')
        ]
        self.level_type.choices = [
            ('DEFAULT', 'Default: Standard world with hills, valleys, water, etc.'),
            ('FLAT', 'Flat: A flat world with no features, meant for building.'),
            ('LARGEBIOMES', 'Large Biomes: Same as default but all biomes are larger.'),
            ('AMPLIFIED', 'Amplified: Same as default but world-generation height limit is increased.')
        ]
        self.difficulty.choices = [
            ('0', 'Peaceful'),
            ('1', 'Easy'),
            ('2', 'Normal'),
            ('3', 'Hard')
        ]
        self.op_permission_level.choices = [
            ('1', 'Can bypass spawn protection'),
            ('2', 'Can use /clear, /difficulty, /effect, /gamemode, /gamerule, /give, and /tp, and can edit command blocks'),
            ('3', 'Can use /ban, /deop, /kick, and /op')
        ]


class ServerCreateGceHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        username = ''
        usernames = self.request.user.usernames
        if usernames:
            username = usernames[0]
        form = ServerPropertiesForm(operator=username)
        context = {'form': form, 'action': webapp2.uri_for('server_create_gce')}
        self.render_template('server_create.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        try:
            form = ServerPropertiesForm(formdata=self.request.POST)
            if form.validate():
                server = Server.create(
                    name=form.name.data,
                    is_gce=True,
                    version=form.version.data,
                    memory=form.memory.data,
                    operator=form.operator.data or None,
                    idle_timeout=form.idle_timeout.data
                )
                mc_properties = server.mc_properties
                for prop in form:
                    if prop.name not in ['name', 'version', 'memory', 'operator', 'idle_timeout']:
                        if prop.type == 'IntegerField' or prop.name in [
                            'gamemode', 'difficulty', 'op_permission_level'
                        ]:
                            if prop.data is not None:
                                setattr(mc_properties, prop.name, int(prop.data))
                        else:
                            setattr(mc_properties, prop.name, prop.data)
                mc_properties.put()
                self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))
        except Exception, e:
            logging.error(u"Error POSTing GCE server: {0}".format(e))
            self.abort(404)
        context = {'form': form, 'action': webapp2.uri_for('server_create_gce')}
        self.render_template('server_create.html', context=context)


class ServerEditGceHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            if not server.is_gce:
                self.redirect(webapp2.uri_for('server', key=server.key.urlsafe()))
            form = ServerPropertiesForm(
                obj=server.mc_properties,
                name=server.name,
                version=server.version,
                memory=server.memory,
                operator=server.operator or '',
                idle_timeout=server.idle_timeout
            )
        except Exception, e:
            logging.error(u"Error GETting GCE server: {0}".format(e))
            self.abort(404)
        context = {
            'edit_server': server,
            'form': form,
            'action': webapp2.uri_for('server_gce', key=server.key.urlsafe())
        }
        self.render_template('server.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            form = ServerPropertiesForm(formdata=self.request.POST, server=server)
            if form.validate():
                server.is_gce = True
                server.name = form.name.data
                server.version = form.version.data
                server.memory = form.memory.data
                server.operator = form.operator.data or None
                server.idle_timeout = form.idle_timeout.data
                server.put()
                mc_properties = server.mc_properties
                for prop in form:
                    if prop.name not in ['name', 'version', 'memory', 'operator', 'idle_timeout']:
                        if prop.name == 'server_port':
                            if prop.data is not None:
                                setattr(mc_properties, prop.name, int(prop.data))
                            else:
                                setattr(mc_properties, prop.name, None)
                        elif prop.type == 'IntegerField' or prop.name in [
                            'gamemode', 'difficulty', 'op_permission_level'
                        ]:
                            setattr(mc_properties, prop.name, int(prop.data))
                        else:
                            setattr(mc_properties, prop.name, prop.data)
                mc_properties.put()
                self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))
        except Exception, e:
            logging.error(u"Error POSTing GCE server: {0}".format(e))
            self.abort(404)
        context = {
            'edit_server': server,
            'form': form,
            'action': webapp2.uri_for('server_gce', key=server.key.urlsafe())
        }
        self.render_template('server.html', context=context)


class ServerDeactivateHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            server.deactivate()
        except Exception, e:
            logging.error(u"Error deactivating server: {0}".format(e))
        self.redirect(webapp2.uri_for('admin'))


class ServerStartHandler(AdminHandlerBase):
    @authentication_required(authenticate=authenticate)
    def post(self, key):
        server = self.get_server_by_key(key, abort=False)
        if server is None:
            self.redirect_to_server('home')
            return
        try:
            server.start()
        except Exception, e:
            logging.error(u"Error starting server: {0}".format(e))
        self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))


class ServerStopHandler(AdminHandlerBase):
    @authentication_required(authenticate=authenticate)
    def post(self, key):
        server = self.get_server_by_key(key, abort=False)
        if server is None:
            self.redirect_to_server('home')
            return
        try:
            server.stop()
        except Exception, e:
            logging.error(u"Error stopping server: {0}".format(e))
        self.redirect(webapp2.uri_for('home', server_key=server.key.urlsafe()))


class MinecraftDownloadForm(form.Form):
    version = fields.StringField(u'Version', validators=[validators.DataRequired(), UniqueVersion()])
    url = fields.StringField(u'Download URL', validators=[validators.URL(), VersionUrlExists()])


class MinecraftDownloadCreateHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        form = MinecraftDownloadForm()
        context = {'form': form}
        self.render_template('version.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        form = MinecraftDownloadForm(self.request.POST)
        if form.validate():
            download = MinecraftDownload.create(form.version.data, form.url.data)
            download.put()
            self.redirect(webapp2.uri_for('admin'))
        context = {'form': form}
        self.render_template('version.html', context=context)


class InstanceForm(form.Form):
    zone = fields.SelectField(u'Zone', validators=[validators.DataRequired()])
    machine_type = fields.SelectField(u'Machine Type', validators=[validators.DataRequired()])
    reserved_ip = fields.BooleanField(u'Use Reserved IP Address')

    def __init__(self, *args, **kwargs):
        super(InstanceForm, self).__init__(*args, **kwargs)
        self.zone.choices = [(z, z) for z in gce.get_zones() or []]
        self.machine_type.choices = [
            ('f1-micro', '1 vCPU (shared physical core) and 0.6 GB RAM @ $0.019/Hour'),
            ('g1-small', '1 vCPU (shared physical core) and 1.7 GB RAM @ $0.054/Hour'),
            ('n1-standard-1', '1 vCPU, 3.75 GB RAM'),
            ('n1-highcpu-2', '2 vCPUs, 1.8 GB RAM'),
            ('n1-standard-2', '2 vCPUs, 7.5 GB RAM'),
            ('n1-highcpu-4', '4 vCPUs, 3.6 GB RAM'),
            ('n1-standard-4', '4 vCPUs, 15 GB RAM'),
            ('n1-highcpu-8', '8 vCPUs, 7.2 GB RAM'),
            ('n1-standard-8', '8 vCPUs, 30 GB RAM')
        ]


class InstanceConfigureHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        instance = gce.Instance.singleton()
        form = InstanceForm(obj=instance)
        context = {'form': form, 'instance': instance}
        self.render_template('instance_configure.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        form = InstanceForm(self.request.POST)
        if form.validate():
            instance = gce.Instance.singleton()
            instance.zone = form.zone.data
            instance.machine_type = form.machine_type.data
            instance.reserved_ip = form.reserved_ip.data
            instance.put()
            self.redirect(webapp2.uri_for('admin'))
        context = {'form': form}
        self.render_template('instance_configure.html', context=context)


class InstanceStartHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        instance = gce.Instance.singleton()
        instance.start()
        self.redirect(webapp2.uri_for('admin'))


class InstanceStopHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        instance = gce.Instance.singleton()
        instance.stop()
        self.redirect(webapp2.uri_for('admin'))


class ServerLogHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None or ON_SERVER:
                self.abort(404)
        except Exception:
            self.abort(404)
        context = {'edit_server': server, 'action': webapp2.uri_for('server_upload_log', key=server.key.urlsafe())}
        self.render_template('server_log.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None or ON_SERVER:
                self.abort(404)
            file = self.request.POST['file']
            import StringIO
            from models import LogLine
            buf = StringIO.StringIO(file.value)
            for raw_line in buf.readlines():
                line = raw_line.decode('ISO-8859-2', errors='ignore')
                line = line.strip()
                existing_line = LogLine.lookup_line(server.key, line)
                if existing_line is None:
                    log_line = LogLine.create(server, line, 'UTC')
                    logging.info(log_line.line)
        except Exception, e:
            logging.error(u"Error POSTing server: {0}".format(e))
            self.abort(404)
        context = {'edit_server': server, 'form': form, 'action': webapp2.uri_for('server_upload_log', key=server.key.urlsafe())}
        self.render_template('server_log.html', context=context)


routes = [
    RedirectRoute('/admin', handler=AdminHandler, strict_slash=True, name="admin"),
    RedirectRoute('/admin/users', handler=UsersHandler, strict_slash=True, name="users"),
    RedirectRoute('/admin/users/<key>', handler=UserEditHandler, strict_slash=True, name="user"),
    RedirectRoute('/admin/users/<key>/remove', handler=UserRemoveHandler, strict_slash=True, name="user_remove"),
    RedirectRoute('/admin/server_create', handler=ServerCreateHandler, strict_slash=True, name="server_create"),
    RedirectRoute('/admin/server_create_gce', handler=ServerCreateGceHandler, strict_slash=True, name="server_create_gce"),
    RedirectRoute('/admin/servers/<key>', handler=ServerEditHandler, strict_slash=True, name="server"),
    RedirectRoute('/admin/servers/<key>/gce', handler=ServerEditGceHandler, strict_slash=True, name="server_gce"),
    RedirectRoute('/admin/servers/<key>/deactivate', handler=ServerDeactivateHandler, strict_slash=True, name="server_deactivate"),
    RedirectRoute('/admin/servers/<key>/start', handler=ServerStartHandler, strict_slash=True, name="server_start"),
    RedirectRoute('/admin/servers/<key>/stop', handler=ServerStopHandler, strict_slash=True, name="server_stop"),
    RedirectRoute('/admin/servers/<key>/upload_log', handler=ServerLogHandler, strict_slash=True, name="server_upload_log"),
    RedirectRoute('/admin/minecraft_create', handler=MinecraftDownloadCreateHandler, strict_slash=True, name="minecraft_create"),
    RedirectRoute('/admin/instance/configure', handler=InstanceConfigureHandler, strict_slash=True, name="instance_configure"),
    RedirectRoute('/admin/instance/start', handler=InstanceStartHandler, strict_slash=True, name="instance_start"),
    RedirectRoute('/admin/instance/stop', handler=InstanceStopHandler, strict_slash=True, name="instance_stop"),
]
