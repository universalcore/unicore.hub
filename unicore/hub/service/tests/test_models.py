from unicore.hub.service.tests import DBTestCase
from unicore.hub.service.models import ModelException


class AppModelTestCase(DBTestCase):

    def test_slug_generation(self):
        # in one transaction
        app1 = self.create_app(self.db, title='foo', password='password')
        app2 = self.create_app(self.db, title='foo', password='password')
        app3 = self.create_app(self.db, title='foobar', password='password')
        self.db.commit()
        # NOTE: don't assume order of slug generation
        self.assertEqual({app1.slug, app2.slug},
                         {'foo', 'foo-2'})
        self.assertEqual(app3.slug, 'foobar')

        # in another transaction
        app4 = self.create_app(self.db, title='foobar', password='password')
        self.db.commit()
        self.assertEqual(app4.slug, 'foobar-2')

        # no title from wich to generate slug
        with self.assertRaises(ModelException):
            self.create_app(self.db, password='password')
            self.db.commit()


class UserModelTestCase(DBTestCase):
    pass
