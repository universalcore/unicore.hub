from urlparse import urlparse, parse_qs

from pyramid.testing import DummyRequest, setUp, tearDown

from mock import Mock

from unicore.hub.service.sso.models import TICKET_RE
from unicore.hub.service.sso.tests import SSOTestCase
from unicore.hub.service.sso.views import BaseView
from unicore.hub.service.sso.utils import clean_url


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

    def test_login(self):
        self.create_user(self.db, username='foo', password='password')
        self.db.flush()
        service = 'http://domain.com'

        # normal get request when logged out
        resp = self.app.get('/sso/login')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input type="text" name="username"', resp.body)
        self.assertIn('<input type="password" name="password"', resp.body)

        # gateway request when logged out
        self.app.reset()
        resp = self.app.get(
            '/sso/login', params={'service': service, 'gateway': True})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.headers['Location'], service)

        # login - no service parameter
        self.app.reset()
        resp = self.app.post('/sso/login', params={
            'username': 'foo',
            'password': 'password',
            'submit': 'submit'})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(
            resp.headers['Location'], 'http://localhost/sso/login')
        self.assertIn('beaker.session.id', resp.headers.get('Set-Cookie'))

        # login - service parameter
        self.app.reset()
        resp = self.app.post('/sso/login?service=%s' % service, params={
            'username': 'foo',
            'password': 'password',
            'submit': 'submit'})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.headers['Location']), service)
        query = parse_qs(urlparse(resp.headers['Location']).query)
        self.assertIn('ticket', query)
        self.assertTrue(TICKET_RE.match(query['ticket'][0]))

        # renew when logged in
        resp = self.app.get('/sso/login', params={'renew': True})
        self.assertEqual(resp.status_int, 200)

        # gateway request when logged in
        resp = self.app.get(
            '/sso/login', params={'service': service, 'gateway': True})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.headers['Location']), service)
        query = parse_qs(urlparse(resp.headers['Location']).query)
        self.assertIn('ticket', query)

        # normal get with service when logged in
        resp = self.app.get('/sso/login', params={'service': service})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.headers['Location']), service)
        query = parse_qs(urlparse(resp.headers['Location']).query)
        self.assertIn('ticket', query)

        # normal get without service when logged in
        resp = self.app.get('/sso/login')
        self.assertEqual(resp.status_int, 200)
        # TODO
        # self.assertIn('You are logged in as', resp.body)

        # login with missing fields
        self.app.reset()
        resp = self.app.post('/sso/login', params={'submit': 'submit'})
        self.assertEqual(resp.status_int, 200)
        self.assertIn('Required', resp.body)

        # login with bad credentials
        resp = self.app.post('/sso/login?service=%s' % service, params={
            'username': 'foo',
            'password': 'password2',
            'submit': 'submit'})
        self.assertEqual(resp.status_int, 200)
        self.assertIn('Username or password is incorrect', resp.body)
