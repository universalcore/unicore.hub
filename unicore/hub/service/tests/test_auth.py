from unicore.hub.service.tests import DBTestCase


class AuthTestCase(DBTestCase):

    def test_app_authentication(self):

        def requestUser(credentials=None):
            if credentials:
                return self.app.get(
                    '/users/1',
                    headers=self.get_basic_auth_header(*credentials),
                    expect_errors=True)
            return self.app.get('/users/1', expect_errors=True)

        # not authenticated
        self.assertEqual(requestUser().status_int, 401)
        self.assertEqual(requestUser(('foo', 'password')).status_int, 401)
        app = self.create_app(self.db, title='foo', password='password')
        self.db.commit()
        self.assertEqual(requestUser((app.slug, 'password2')).status_int, 401)

        # authenticated (user doesn't exist)
        self.assertEqual(requestUser((app.slug, 'password')).status_int, 404)

    def test_user_authentication(self):
        pass  # TODO
