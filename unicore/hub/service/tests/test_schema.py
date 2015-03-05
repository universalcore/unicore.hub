from unittest import TestCase
from uuid import uuid4

import colander

from unicore.hub.service.schema import (User as UserSchema,
                                        App as AppSchema)


MINIMAL_USER_DATA = {
    'username': 'foo',
    'password': '1234',
}
MINIMAL_APP_DATA = {
    'title': 'Foo'
}


class UserSchemaTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schema = UserSchema()

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
