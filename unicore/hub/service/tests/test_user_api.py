from unicore.hub.service.models import User
from unicore.hub.service.tests import DBTestCase


class UserApiTestCase(DBTestCase):

    def test_get(self):
        app_data = {2: {'some_random_datapoint': 'stuff'}}
        user = self.create_user(self.db, app_data=app_data)
        app = self.create_app(self.db, password='password')
        self.db.commit()

        # no data for app
        resp = self.app.get(
            '/users/%s' % user.id,
            headers=self.get_basic_auth_header(app.id, 'password'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json, {})

        app_data[app.id] = {'display_name': 'foo_display'}
        user.app_data = app_data
        self.db.commit()

        # with data
        resp = self.app.get(
            '/users/%s' % user.id,
            headers=self.get_basic_auth_header(app.id, 'password'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json, app_data[app.id])

    def test_post(self):
        user = self.create_user(self.db)
        app = self.create_app(self.db, password='password')
        self.db.commit()
        app_data = {'display_name': 'foo_display'}

        # no app data yet
        resp = self.app.post_json(
            '/users/%s' % user.id,
            params=app_data,
            headers=self.get_basic_auth_header(app.id, 'password'))
        self.db.expire_all()
        user = self.db.query(User).get(user.id)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(user.app_data.values()[0], app_data)

        # with existing app data
        app_data = {'display_name': 'foo_display_new'}
        resp = self.app.post_json(
            '/users/%s' % user.id,
            params=app_data,
            headers=self.get_basic_auth_header(app.id, 'password'))
        self.db.expire_all()
        user = self.db.query(User).get(user.id)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(user.app_data.values()[0], app_data)
