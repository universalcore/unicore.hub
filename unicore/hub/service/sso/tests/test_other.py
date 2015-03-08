from unittest import TestCase

from unicore.hub.service.tests import DBTestCase
from unicore.hub.service.sso.utils import make_redirect


class TicketModelTestCase(DBTestCase):
    pass


class UtilsTestCase(TestCase):

    def test_make_redirect(self):
        self.assertEqual(make_redirect(
            'http://domain.com/', params={'param1': '1'}).location,
            'http://domain.com/?param1=1')
