from unicore.hub.service.models import App
from unicore.hub.service.tests import DBTestCase


class AppApiTestCase(DBTestCase):
    minimal_app_attrs = {
        'title': 'title',
        'key': 'key'
    }

    def setUp(self):
        super(AppApiTestCase, self).setUp()
        self.manager_app = self.create_app(
            self.db, title='foo', key='key', url='http://www.example.com',
            groups=['group:apps_manager'])
        self.user_app = self.create_app(
            self.db, title='foo', key='key', url='http://www.example.com')
        self.db.commit()

    def test_view(self):
        resp = self.app.get(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'key'))
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, self.user_app.to_dict())

    def test_edit(self):
        # change non-privileged fields
        resp = self.app.put_json(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'key'),
            params={'title': 'foo2', 'url': 'http://www.example2.com'})
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, new_user_app.to_dict())
        self.assertEqual('foo2', new_user_app.title)
        self.assertEqual('http://www.example2.com', new_user_app.url)

        # change group
        resp = self.app.put_json(
            '/apps/%s' % self.user_app.uuid,
            headers=self.get_basic_auth_header(
                self.manager_app.uuid, 'key'),
            params={'title': 'foo', 'groups': ['group:apps_manager']})
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body, new_user_app.to_dict())
        self.assertEqual(['group:apps_manager'], new_user_app.groups)

    def test_create(self):
        data = {
            'title': 'foobar',
            'groups': ['group:apps_manager'],
            'url': 'http://www.example.com'}
        resp = self.app.post_json(
            '/apps',
            headers=self.get_basic_auth_header(
                self.manager_app.uuid, 'key'),
            params=data)
        self.assertEqual(resp.json_body['title'], data['title'])
        self.assertEqual(resp.json_body['groups'], data['groups'])
        self.assertEqual(resp.json_body['url'], data['url'])
        new_app = self.db.query(App).get(resp.json_body['uuid'])
        self.assertEqual(resp.json_body, new_app.to_dict())

    def test_reset_key(self):
        resp = self.app.put(
            '/apps/%s/reset_key' % self.user_app.uuid,
            headers=self.get_basic_auth_header(self.user_app.uuid, 'key'))
        self.db.expire_all()
        new_user_app = self.db.query(App).get(self.user_app.uuid)
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.json_body['key'], new_user_app.key)
        self.assertNotEqual('key', new_user_app.key)
