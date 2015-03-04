from unittest import TestCase

from unicore.hub.service import utils


class UtilsTestCase(TestCase):

    def test_make_password(self):
        for l in range(1, 20):
            password = utils.make_password(bit_length=l)
            self.assertTrue(len(password) > l)

    def test_make_slugs(self):
        slugs = ['foo', 'foo-2', 'foo-3', 'foo-4']
        generator = utils.make_slugs('foo')
        for i in range(4):
            self.assertEqual(next(generator), slugs[i])
