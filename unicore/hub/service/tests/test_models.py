import uuid

from unicore.hub.service.tests import DBTestCase


class AppModelTestCase(DBTestCase):

    def test_uuid(self):
        app = self.create_app(self.db, title='Foo', password='password')
        self.db.flush()
        the_uuid = app._uuid
        self.assertEqual(the_uuid, uuid.UUID(app.uuid))
        app.uuid = app.uuid
        self.assertEqual(the_uuid, app._uuid)


class UserModelTestCase(DBTestCase):

    def test_uuid(self):
        user = self.create_user(self.db)
        self.db.flush()
        the_uuid = user._uuid
        self.assertEqual(the_uuid, uuid.UUID(user.uuid))
        user.uuid = user.uuid
        self.assertEqual(the_uuid, user._uuid)
