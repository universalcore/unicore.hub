from urlparse import urlparse, parse_qs

from pyramid.testing import DummyRequest, setUp, tearDown

from mock import Mock, patch

from unicore.hub.service.sso.models import TICKET_RE, Ticket
from unicore.hub.service.sso.tests import SSOTestCase
from unicore.hub.service.sso.views import BaseView, CASViews
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
        self.assertIn('You are logged in as foo', resp.body)

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

    def test_logout(self):
        service = 'http://example.com'
        user = self.create_user(self.db, username='foo', password='password')
        self.db.flush()
        [self.create_ticket(self.db, user_id=user.uuid, service=service)
         for i in range(10)]
        self.db.flush()

        resp = self.app.post('/sso/login?service=%s' % service, params={
            'username': 'foo',
            'password': 'password',
            'submit': 'submit'})
        self.assertEqual(resp.status_int, 302)

        resp = self.app.get('/sso/logout')
        # logout consumes all tickets
        self.assertEqual(
            self.db.query(Ticket)
            .filter(Ticket.user_id == user.uuid)
            .filter(Ticket.consumed.is_(None))
            .count(), 0)
        self.assertEqual(
            self.db.query(Ticket)
            .filter(Ticket.user_id == user.uuid)
            .filter(Ticket.consumed.isnot(None))
            .count(), 11)
        # correct text is displayed
        self.assertIn('You have been logged out successfully', resp.body)

        # session is no longer authenticated
        with patch.object(CASViews, 'login_get') as mock_login_get, \
                patch.object(CASViews, '__init__') as mock_init:
            mock_login_get.return_value = {}
            mock_init.return_value = None
            self.app.get('/sso/login')
            self.assertNotIn('auth.userid', mock_init.call_args[0][0].session)
