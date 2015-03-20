from unittest import TestCase
from uuid import uuid4

import colander
from mock import Mock

from unicore.hub.service.tests import DBTestCase
from unicore.hub.service.schema import (User as UserSchema,
                                        App as AppSchema)


MINIMAL_USER_DATA = {
    'username': 'foo',
    'password': '1234',
}
MINIMAL_APP_DATA = {
    'title': 'Foo'
}


class UserSchemaTestCase(DBTestCase):

    def setUp(self):
        super(UserSchemaTestCase, self).setUp()
        request = Mock(db=self.db)
        self.schema = UserSchema().bind(request=request)

    def test_field_existence(self):
        for field in MINIMAL_USER_DATA.keys():
            incomplete_data = MINIMAL_USER_DATA.copy()
            del incomplete_data[field]
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize(incomplete_data)

    def test_app_data_validation(self):
        user_data = MINIMAL_USER_DATA.copy()
        uuid = uuid4().hex
        app_data = {
            uuid: {
                'display_name': 'foo'
            }
        }
        user_data['app_data'] = app_data
        self.assertEqual(self.schema.deserialize(user_data)['app_data'],
                         app_data)

        for app_id in ('abcd', -1, 10.5, ()):
            user_data['app_data'] = {app_id: {}}
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize(user_data)

    def test_pin_validation(self):
        user_data = MINIMAL_USER_DATA.copy()

        for invalid in (1, (), '123', '123a', '12345'):
            user_data['password'] = invalid
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize(user_data)

        user_data['password'] = '1234'
        self.schema.deserialize(user_data)

    def test_username_validation(self):
        self.create_user(self.db, username='foo', password='password')
        self.db.flush()

        invalid_usernames = [
            (u'foo\u001e', 'contains control characters'),
            (u'foo\u202b', 'contains control characters'),
            (' foo', 'has leading space'),
            ('foo ', 'has trailing space'),
            ('hello   world', 'more than 1 space in a row'),
            ('foo', 'is not unique'),
            ('', 'Required'),
            ('a' * 256, 'Longer than maximum')
        ]

        user_data = MINIMAL_USER_DATA.copy()
        for invalid_username, msg in invalid_usernames:
            user_data['username'] = invalid_username
            with self.assertRaisesRegexp(colander.Invalid, msg):
                self.schema.deserialize(user_data)


class AppSchemaTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schema = AppSchema()

    def test_field_existence(self):
        for field in MINIMAL_APP_DATA.keys():
            incomplete_data = MINIMAL_APP_DATA.copy()
            del incomplete_data[field]
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize(incomplete_data)

    def test_groups_validation(self):
        data = self.schema.deserialize(MINIMAL_APP_DATA)
        self.assertEqual(data['groups'], [])

        data = MINIMAL_APP_DATA.copy()
        data['groups'] = ['group:apps_manager']
        data = self.schema.deserialize(data)
        self.assertEqual(data['groups'], ['group:apps_manager'])

        for invalid in (['groups:apps_manager', 'something_else'], [124]):
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize({'groups': invalid})

    def test_title_validation(self):
        app_data = MINIMAL_APP_DATA.copy()
        app_data['title'] = 'a' * 256
        with self.assertRaisesRegexp(colander.Invalid, 'Longer than maximum'):
            self.schema.deserialize(app_data)

    def test_url_validation(self):
        app_data = MINIMAL_APP_DATA.copy()
        app_data['url'] = 'thisisnotaurl'
        with self.assertRaisesRegexp(colander.Invalid, 'Must be a URL'):
            self.schema.deserialize(app_data)
