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
        self.assertEqual(requestUser((1, 'password')).status_int, 401)
        self.create_app(self.db, id=1, password='password')
        self.db.commit()
        self.assertEqual(requestUser((1, 'password2')).status_int, 401)

        # authenticated (user doesn't exist)
        self.assertEqual(requestUser((1, 'password')).status_int, 404)

    def test_user_authentication(self):
        pass  # TODO
