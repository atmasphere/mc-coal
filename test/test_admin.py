import fix_dev_path

import logging

import minimock


import gce
from main_test import AuthTest
from models import Server, MinecraftDownload
from oauth import Client


TEST_USER_EMAIL = 'test@example.com'


class AdminAuthTest(AuthTest):
    def test_get_auth(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_admin()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_get_inactive_user(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user(email="admin@example.com", is_admin=True)
            self.log_out_user()
            super(AdminAuthTest, self).test_get_inactive_user()

    def test_get_login_again(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_admin()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get()
            self.assertRedirects(response)
            self.log_in_admin()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_get_logout(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_admin()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get()
            self.assertRedirects(response)

    def test_get_not_admin(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user(email="admin@example.com", is_admin=True)
            self.log_out_user()
            self.log_in_user()
            response = self.get()
            self.assertRedirects(response)


class AdminTest(AdminAuthTest):
    URL = '/admin'

    def setUp(self):
        super(AdminTest, self).setUp()
        logging.disable(logging.ERROR)

    def test_get_first_user(self):
        self.log_in_user()
        self.assertFalse(self.current_user.admin)
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.assertTrue(self.current_user.admin)

    def tearDown(self):
        super(AdminTest, self).tearDown()
        logging.disable(logging.NOTSET)


class UsersTest(AdminAuthTest):
    URL = '/admin/users'


class UserEditTest(AdminAuthTest):
    URL = '/admin/users/{0}'

    def setUp(self):
        super(UserEditTest, self).setUp()
        self.log_in_user("user@test.com")
        self.user = self.current_user
        self.user.usernames = ['username1, username2']
        self.user.put()
        self.log_out_user()

    @property
    def url(self):
        return self.URL.format(self.user.key.urlsafe())

    def test_get_multiple_usernames(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)


class ServerCreateTest(AdminAuthTest):
    URL = '/admin/server_create'

    def test_post(self):
        self.server.key.delete()
        self.log_in_admin()
        self.assertEqual(0, Server.query().count())
        self.assertEqual(0, Client.query().count())
        response = self.post(params={'name': 'new server'})
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = Server.query().get()
        self.assertEqual('new server', server.name)
        self.assertEqual(False, server.is_gce)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))


class ServerCreateGceTest(AdminAuthTest):
    URL = '/admin/server_create_gce'

    def test_post(self):
        mc = MinecraftDownload.create(
            '1.7.4',
            'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.key.delete()
        self.log_in_admin()
        self.assertEqual(0, Server.query().count())
        self.assertEqual(0, Client.query().count())
        response = self.post(params={
            'name': 'new server',
            'version': mc.version,
            'memory': '1G',
            'motd': 'Welcome',
            'white_list': True,
            'idle_timeout': 10
        })
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = Server.query().get()
        self.assertEqual('new server', server.name)
        self.assertEqual(True, server.is_gce)
        self.assertEqual('1G', server.memory)
        self.assertEqual(10, server.idle_timeout)
        mc_properties = server.mc_properties
        self.assertEqual('Welcome', mc_properties.motd)
        self.assertEqual(True, mc_properties.white_list)
        self.assertEqual(None, mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))

    def test_post_port(self):
        mc = MinecraftDownload.create(
            '1.7.4',
            'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.key.delete()
        self.log_in_admin()
        self.assertEqual(0, Server.query().count())
        self.assertEqual(0, Client.query().count())
        response = self.post(params={
            'name': 'new server',
            'version': mc.version,
            'memory': '1G',
            'motd': 'Welcome',
            'white_list': True,
            'server_port': 25565,
            'idle_timeout': 10
        })
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = Server.query().get()
        self.assertEqual('new server', server.name)
        self.assertEqual(True, server.is_gce)
        self.assertEqual('1G', server.memory)
        mc_properties = server.mc_properties
        self.assertEqual('Welcome', mc_properties.motd)
        self.assertEqual(True, mc_properties.white_list)
        self.assertEqual(25565, mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))

    def test_post_non_unique_port(self):
        mc = MinecraftDownload.create(
            '1.7.4',
            'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.key.delete()
        self.log_in_admin()
        self.assertEqual(0, Server.query().count())
        self.assertEqual(0, Client.query().count())
        response = self.post(params={
            'name': 'new server',
            'version': mc.version,
            'memory': '1G',
            'motd': 'Welcome',
            'white_list': True,
            'server_port': 25565,
            'idle_timeout': 10
        })
        response = self.post(params={
            'name': 'new server',
            'version': mc.version,
            'memory': '1G',
            'motd': 'Welcome',
            'white_list': True,
            'server_port': 25565,
            'idle_timeout': 10
        })
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        self.assertOK(response)

    def test_post_idle_timeout(self):
        mc = MinecraftDownload.create(
            '1.7.4',
            'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.key.delete()
        self.log_in_admin()
        self.assertEqual(0, Server.query().count())
        self.assertEqual(0, Client.query().count())
        response = self.post(params={
            'name': 'new server',
            'version': mc.version,
            'memory': '1G',
            'motd': 'Welcome',
            'white_list': True,
            'server_port': 25565,
            'idle_timeout': 0
        })
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = Server.query().get()
        self.assertEqual('new server', server.name)
        self.assertEqual(True, server.is_gce)
        self.assertEqual('1G', server.memory)
        self.assertEqual(0, server.idle_timeout)
        mc_properties = server.mc_properties
        self.assertEqual('Welcome', mc_properties.motd)
        self.assertEqual(True, mc_properties.white_list)
        self.assertEqual(25565, mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))


class ServerKeyTest(AdminAuthTest):
    URL = '/admin/servers/{0}'

    @property
    def url(self):
        return self.URL.format(self.server.key.urlsafe())

    def test_post(self):
        self.log_in_admin()
        response = self.post(params={'name': 'new name'})
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = self.server.key.get()
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))
        self.assertEqual('new name', server.name)


class ServerKeyGceTest(AdminAuthTest):
    URL = '/admin/servers/{0}/gce'

    def setUp(self):
        super(ServerKeyGceTest, self).setUp()
        self.server.is_gce = True
        self.server.put()

    @property
    def url(self):
        return self.URL.format(self.server.key.urlsafe())

    def test_post(self):
        self.log_in_admin()
        self.mc = MinecraftDownload.create(
            '1.7.4', 'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.version = self.mc.version
        self.server.put()
        response = self.post(
            params={
                'name': 'new name',
                'version': self.server.version,
                'memory': '1G',
                'server_port': 25565,
                'idle_timeout': 10
            }
        )
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = self.server.key.get()
        self.assertEqual('new name', server.name)
        self.assertEqual('1G', server.memory)
        self.assertEqual(25565, server.mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))

    def test_post_duplicate_self_port(self):
        self.server.mc_properties.server_port = 25565
        self.server.mc_properties.put()
        self.log_in_admin()
        self.mc = MinecraftDownload.create(
            '1.7.4', 'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.version = self.mc.version
        self.server.put()
        response = self.post(
            params={
                'name': self.server.name,
                'version': self.server.version,
                'memory': '1G',
                'server_port': 25565,
                'idle_timeout': 10
            }
        )
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = self.server.key.get()
        server = self.server.key.get()
        self.assertEqual(25565, server.mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))

    def test_post_duplicate_none_port(self):
        self.server.mc_properties.server_port = 25565
        self.server.mc_properties.put()
        self.log_in_admin()
        self.mc = MinecraftDownload.create(
            '1.7.4', 'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
        )
        self.server.version = self.mc.version
        self.server.put()
        response = self.post(
            params={
                'name': self.server.name,
                'version': self.server.version,
                'memory': '1G',
                'server_port': '',
                'idle_timeout': 10
            }
        )
        self.assertEqual(1, Server.query().count())
        self.assertEqual(1, Client.query().count())
        server = self.server.key.get()
        server = self.server.key.get()
        self.assertIsNone(server.mc_properties.server_port)
        self.assertRedirects(response, '/servers/{0}'.format(server.key.urlsafe()))


class InstanceConfigureTest(AdminAuthTest):
    URL = '/admin/instance/configure'

    def setUp(self):
        super(InstanceConfigureTest, self).setUp()
        minimock.mock('gce.get_zones', returns=['us-central1-a', 'us-central1-b'], tracker=None)

    def tearDown(self):
        super(InstanceConfigureTest, self).tearDown()
        minimock.restore()

    def test_post(self):
        self.log_in_admin()
        self.assertEqual(0, gce.Instance.query().count())
        zones = gce.get_zones()
        response = self.post(params={'zone': zones[0], 'machine_type': 'f1-micro'})
        self.assertRedirects(response, AdminTest.URL)
        self.assertEqual(1, gce.Instance.query().count())
        instance = gce.Instance.query().get()
        self.assertEqual(zones[0], instance.zone)
        self.assertEqual('f1-micro', instance.machine_type)
