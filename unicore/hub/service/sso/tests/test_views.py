from pyramid.testing import DummyRequest, setUp, tearDown

from mock import Mock

from unicore.hub.service.sso.tests import SSOTestCase
from unicore.hub.service.sso.views import BaseView


class CASViewsTestCase(SSOTestCase):

    def test_locale(self):
        resp = self.app.get('/sso/login')
        self.assertIn('Set-Cookie', resp.headers)
        self.assertIn('_LOCALE_=eng_GB', resp.headers['Set-Cookie'])

        resp = self.app.get('/sso/login')
        self.assertNotIn('Set-Cookie', resp.headers)

        resp = self.app.get('/sso/login?_LOCALE_=tam_IN')
        self.assertIn('Set-Cookie', resp.headers)
        self.assertIn('_LOCALE_=tam_IN', resp.headers['Set-Cookie'])

    def test_make_redirect(self):
        config = setUp()
        config.add_route('user-login', '/sso/login')
        request = DummyRequest()
        request.tmpl_context = Mock()
        view = BaseView(request)

        self.assertEqual(view.make_redirect(
            'http://domain.com/', params={'param1': '1'}).location,
            'http://domain.com/?param1=1')

        request.response.headerlist.extend([('Set-Cookie', 'auth_tkt="bla"')])
        resp = view.make_redirect(route_name='user-login')
        self.assertEqual(resp.location, 'http://example.com/sso/login')
        self.assertIn(('Set-Cookie', 'auth_tkt="bla"'), resp.headerlist)

        tearDown()
