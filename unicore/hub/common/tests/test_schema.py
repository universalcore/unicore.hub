from unittest import TestCase

import colander

from unicore.hub.common.schema import User as UserSchema


MINIMAL_USER_DATA = {
    'user_id': 1234,
    'username': 'foo',
    'app_data': {}
}


class UserSchemaTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schema = UserSchema()

    def test_field_existence(self):
        for field in ('user_id', 'username', 'app_data'):
            incomplete_data = MINIMAL_USER_DATA.copy()
            del incomplete_data[field]
            with self.assertRaises(colander.Invalid):
                self.schema.deserialize(incomplete_data)

        complete_user_data = MINIMAL_USER_DATA.copy()
        complete_user_data.update({
            'msisdn': '1234567890',
            'email': 'foo@foo.com'
        })
        complete_user_data = self.schema.deserialize(complete_user_data)
        for field in ('msisdn', 'email'):
            self.assertIn(field, complete_user_data)

    def test_app_data_validation(self):
        user_data = MINIMAL_USER_DATA.copy()
        app_data = {
            5678: {
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
