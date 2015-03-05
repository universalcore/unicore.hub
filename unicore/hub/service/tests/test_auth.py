from mock import patch
from uuid import uuid4

from unicore.hub.service.tests import DBTestCase


uuid_hex = uuid4().hex


class AuthTestCase(DBTestCase):

    @classmethod
    def setUpClass(cls):
        # NOTE: disabling rollbacks because DBTestCase doesn't use nested
        # transactions for tests yet and 403 causes rollback
        def db(request):
            maker = request.registry.dbmaker
            session = maker()

            def cleanup(request):
                if request.exception is None:
                    session.commit()
                session.close()

            request.add_finished_callback(cleanup)

            return session

        cls.db_patch = patch('unicore.hub.service.db', new=db)
        cls.db_patch.__enter__()

        super(AuthTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(AuthTestCase, cls).tearDownClass()
        cls.db_patch.__exit__(None, None, None)

    def _api_request(self, path, credentials, method, extra):
        if credentials:
            return getattr(self.app, method)(
                path,
                headers=self.get_basic_auth_header(*credentials),
                expect_errors=True, **extra)
        return getattr(self.app, method)(path, expect_errors=True, **extra)

    def request_user(self, credentials=None, method='get', **extra):
        return self._api_request('/users/%s' % uuid_hex, credentials, method, extra).status_int

    def request_app(self, path, credentials=None, method='get', **extra):
        return self._api_request(path, credentials, method, extra).status_int

    def test_authentication(self):
        # not authenticated - user API
        self.assertEqual(self.request_user(), 401)
        self.assertEqual(self.request_user((uuid_hex, 'password')), 401)
        app = self.create_app(self.db, title='foo', password='password')
        self.db.commit()
        self.assertEqual(self.request_user((app.uuid, 'password2')), 401)

        # not authenticated - app API
        self.assertEqual(self.request_app('/apps', method='post'), 401)
        self.assertEqual(self.request_app('/apps/%s' % uuid_hex), 401)
        self.assertEqual(self.request_app('/apps/%s' % uuid_hex, method='put'), 401)
        self.assertEqual(
            self.request_app('/apps/%s/reset_password' % uuid_hex, method='put'), 401)

        # authenticated (user doesn't exist)
        self.assertEqual(self.request_user((app.uuid, 'password')), 404)

    def test_app_api_authorization(self):
        # NOTE: this test is slooooowwww
        app = self.create_app(self.db, title='foo', password='password')
        self.db.flush()

        # not authorized by virtue of not being in group:apps_manager
        self.assertEqual(self.request_app(
            '/apps', (app.uuid, 'password'), 'post'), 403)
        # not authorized by virtue of requesting app data other than its own
        self.assertEqual(self.request_app(
            '/apps/%s' % uuid_hex, (app.uuid, 'password')), 403)
        self.assertEqual(self.request_app(
            '/apps/%s' % uuid_hex, (app.uuid, 'password'), 'put'), 403)
        self.assertEqual(self.request_app(
            '/apps/%s' % uuid_hex, (app.uuid, 'password'), 'put'), 403)
        # authorized by virtue of requesting its own data
        self.assertEqual(self.request_app(
            '/apps/%s' % app.uuid, (app.uuid, 'password')), 200)
        self.assertEqual(self.request_app(
            '/apps/%s' % app.uuid, (app.uuid, 'password'), 'put_json',
            params={'title': 'foo2'}), 200)
        # not authorized by virtue of trying to change group
        self.assertEqual(self.request_app(
            '/apps/%s' % app.uuid, (app.uuid, 'password'), 'put_json',
            params={'title': 'foo2', 'groups': ['group:apps_manager']}), 403)
        self.assertEqual(self.request_app(
            '/apps/%s/reset_password' % app.uuid,
            (app.uuid, 'password'), 'put'), 200)

        app2 = self.create_app(
            self.db, title='foo', password='password',
            groups=['group:apps_manager'])
        self.db.flush()
        # authorized by virtue of group group:apps_manager
        self.assertEqual(self.request_app(
            '/apps', (app2.uuid, 'password'), 'post_json',
            params={'title': 'foo2'}), 201)
        self.assertIn(self.request_app(
            '/apps/%s' % uuid_hex, (app2.uuid, 'password')), (404, 200))
