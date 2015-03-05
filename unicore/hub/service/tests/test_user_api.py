from unicore.hub.service.models import User
from unicore.hub.service.tests import DBTestCase


class UserApiTestCase(DBTestCase):
    minimal_app_attrs = {
        'title': 'title',
        'password': 'password'
    }

    def test_get(self):
        app = self.create_app(self.db, **self.minimal_app_attrs)
        self.db.flush()  # to get uuid
        app_data = {'other_uuid': {'some_random_datapoint': 'stuff'}}
        user = self.create_user(self.db, app_data=app_data)
        self.db.commit()

        # no data for app
        resp = self.app.get(
            '/users/%s' % user.uuid,
            headers=self.get_basic_auth_header(app.uuid, 'password'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json, {})

        app_data[app.uuid] = {'display_name': 'foo_display'}
        user.app_data = app_data
        self.db.commit()

        # with data
        resp = self.app.get(
            '/users/%s' % user.uuid,
            headers=self.get_basic_auth_header(app.uuid, 'password'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json, app_data[app.uuid])

    def test_post(self):
        user = self.create_user(self.db)
        app = self.create_app(self.db, **self.minimal_app_attrs)
        self.db.commit()
        app_data = {'display_name': 'foo_display'}

        # no app data yet
        resp = self.app.post_json(
            '/users/%s' % user.uuid,
            params=app_data,
            headers=self.get_basic_auth_header(app.uuid, 'password'))
        self.db.expire_all()
        user = self.db.query(User).get(user.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(user.app_data.values()[0], app_data)

        # with existing app data
        app_data = {'display_name': 'foo_display_new'}
        resp = self.app.post_json(
            '/users/%s' % user.uuid,
            params=app_data,
            headers=self.get_basic_auth_header(app.uuid, 'password'))
        self.db.expire_all()
        user = self.db.query(User).get(user.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(user.app_data.values()[0], app_data)

    def test_unicode_data(self):
        pass  # TODO
