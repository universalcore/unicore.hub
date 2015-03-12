import re
from unittest import TestCase

from click.testing import CliRunner
from mock import patch, Mock
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.authentication import (BasicAuthAuthenticationPolicy,
                                    SessionAuthenticationPolicy)

from unicore.hub.service import utils
from unicore.hub.service.authentication import PathAuthenticationPolicy
from unicore.hub.service.commands import in_app_env
from unicore.hub.service.models import App
from unicore.hub.service.tests import DBTestCase, get_test_settings, make_app


class UtilsTestCase(TestCase):

    def test_make_password(self):
        for l in range(1, 20):
            password = utils.make_password(bit_length=l)
            self.assertTrue(len(password) > l)

    def test_active_authentication_policy(self):
        app = make_app(*get_test_settings()).app
        policy = app.registry.queryUtility(IAuthenticationPolicy)

        self.assertTrue(isinstance(policy, PathAuthenticationPolicy))

        path_map = [
            ('/sso/login', SessionAuthenticationPolicy),
            ('/sso/logout', SessionAuthenticationPolicy),
            ('/sso/validate', BasicAuthAuthenticationPolicy),
            ('/apps', BasicAuthAuthenticationPolicy),
            ('/users', BasicAuthAuthenticationPolicy)]

        for path, policy_class in path_map:
            self.assertTrue(isinstance(
                policy.get_active_policy(app.request_factory({
                    'REQUEST_METHOD': 'GET', 'PATH_INFO': path})),
                policy_class))


class CommandTestCase(DBTestCase):

    @classmethod
    def setUpClass(cls):
        super(CommandTestCase, cls).setUpClass()
        cls.runner = CliRunner()

    def setUp(self):
        super(CommandTestCase, self).setUp()
        mock_bootstrap = Mock(return_value={'request': Mock(db=self.db)})
        self.patch_bootstrap = patch(
            'unicore.hub.service.commands.bootstrap',
            new=mock_bootstrap)
        self.patch_bootstrap.start()

    def tearDown(self):
        super(CommandTestCase, self).tearDown()
        self.patch_bootstrap.stop()

    def invoke_app_env_command(self, command, args, **kwargs):
        default_kwargs = {'catch_exceptions': False}
        default_kwargs.update(kwargs)
        return self.runner.invoke(
            in_app_env,
            [self.config_file_path, command] + args,
            **default_kwargs)

    def test_create_app_command(self):
        result = self.invoke_app_env_command('create_app', ['Foo'])
        output_re = \
            r"App '[^']+' has been created and assigned to \(.*\)\n" \
            r"App identifier is '\w{32}'\n" \
            r"App password is '.{20}'"

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(re.search(output_re, result.output))
        app = self.db.query(App).filter(App.title == 'Foo').first()
        self.assertTrue(app)
        self.assertNotIn(None, app.to_dict().values())
        self.assertTrue(app.password)

        result = self.invoke_app_env_command(
            'create_app', ['Foo2', '--group', 'group:apps_manager'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('group:apps_manager', result.output)
        app = self.db.query(App).filter(App.title == 'Foo2').first()
        self.assertTrue(app)
        self.assertEqual(app.groups, ['group:apps_manager'])

        result = self.invoke_app_env_command(
            'create_app', ['Foo', '--group', 'group_does_not_exist'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Invalid value for "--group"', result.output)
