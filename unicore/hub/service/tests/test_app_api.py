from unicore.hub.service.models import App
from unicore.hub.service.tests import DBTestCase


class AppApiTestCase(DBTestCase):
    minimal_app_attrs = {
        'title': 'title',
        'password': 'password'
    }

    def setUp(self):
        super(AppApiTestCase, self).setUp()
        self.manager_app = self.create_app(
            self.db, title='foo', password='password',
            groups=['group:apps_manager'])
        self.user_app = self.create_app(
            self.db, title='foo', password='password')
        self.db.commit()

    def test_view(self):
        resp = self.app.get(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'password'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, self.user_app.to_dict())

    def test_edit(self):
        # change non-privileged fields
        resp = self.app.put_json(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'password'),
            params={'title': 'foo2'})
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, new_user_app.to_dict())
        self.assertEqual('foo2', new_user_app.title)

        # change group
        resp = self.app.put_json(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(
                self.manager_app.uuid, 'password'),
            params={'title': 'foo', 'groups': ['group:apps_manager']})
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, new_user_app.to_dict())
        self.assertEqual(['group:apps_manager'], new_user_app.groups)

    def test_create(self):
        data = {'title': 'foobar', 'groups': ['group:apps_manager']}
        resp = self.app.post_json(
            '/apps',
            headers=self.get_basic_auth_header(
                self.manager_app.uuid, 'password'),
            params=data)
        self.assertEqual(resp.json_body['title'], data['title'])
        self.assertEqual(resp.json_body['groups'], data['groups'])
        new_app = self.db.query(App).get(resp.json_body['uuid'])
        body_without_password = resp.json_body
        del body_without_password['password']
        self.assertEqual(body_without_password, new_app.to_dict())

    def test_reset_password(self):
        resp = self.app.put(
            '/apps/%s/reset_password' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'password'))
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body['password'], new_user_app.password)
        self.assertNotEqual('password', new_user_app.password)
