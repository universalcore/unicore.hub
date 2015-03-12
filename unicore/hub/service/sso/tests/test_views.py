from urlparse import urlparse, parse_qs
from urllib import urlencode
from datetime import datetime, timedelta

from pyramid.testing import DummyRequest, setUp, tearDown

from mock import Mock, patch

from unicore.hub.service.models import User
from unicore.hub.service.sso.models import TICKET_RE, Ticket, \
    InvalidTicket, InvalidRequest, InvalidService
from unicore.hub.service.sso.tests import SSOTestCase
from unicore.hub.service.sso.views import BaseView, CASViews, \
    deferred_csrf_validator
from unicore.hub.service.sso.utils import clean_url


class CASViewsTestCase(SSOTestCase):

    @classmethod
    def setUpClass(cls):
        super(CASViewsTestCase, cls).setUpClass()
        validator = Mock()
        validator.return_value = Mock()
        cls.patch_csrf_validator = patch.object(
            deferred_csrf_validator, 'wrapped', new=validator)
        cls.patch_csrf_validator.start()

    @classmethod
    def tearDownClass(cls):
        super(CASViewsTestCase, cls).tearDownClass()
        cls.patch_csrf_validator.stop()

    def test_locale(self):
        resp = self.app.get('/sso/login')
        locale_cookie = filter(
            lambda x: x[0] == 'Set-Cookie' and '_LOCALE_=eng_GB' in x[1],
            resp.headers.iteritems())
        self.assertEqual(len(locale_cookie), 1)

        resp = self.app.get('/sso/login')
        self.assertNotIn('Set-Cookie', resp.headers)

        resp = self.app.get('/sso/login?_LOCALE_=tam_IN')
        self.assertIn('Set-Cookie', resp.headers)
        self.assertIn('_LOCALE_=tam_IN', resp.headers['Set-Cookie'])

    def test_make_redirect(self):
        config = setUp()
        config.add_route('user-login', '/sso/login')
        request = DummyRequest()
        qs = {
            'service': 'http://example.com',
            'gateway': 'true',
            'renew': 'false'}
        request.query_string = qs
        qs = urlencode(qs)
        request.tmpl_context = Mock()
        view = BaseView(request)

        self.assertEqual(view.make_redirect(
            'http://domain.com/', params={'param1': '1'}).location,
            'http://domain.com/?param1=1')

        request.response.headerlist.extend([('Set-Cookie', 'auth_tkt="bla"')])
        resp = view.make_redirect(route_name='user-login')
        self.assertEqual(resp.location, '/sso/login?%s' % qs)
        self.assertIn(('Set-Cookie', 'auth_tkt="bla"'), resp.headerlist)

        tearDown()

    def test_login(self):
        self.create_user(self.db, username='foo', password='password')
        self.db.flush()
        service = 'http://domain.com'
        service_qs = urlencode({'service': service})

        # normal get request when logged out
        resp = self.app.get('/sso/login')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input type="text" name="username"', resp.body)
        self.assertIn('<input type="password" name="password"', resp.body)
        self.assertIn('<input type="hidden" name="lt"', resp.body)

        # gateway request when logged out
        self.app.reset()
        resp = self.app.get(
            '/sso/login', params={'service': service, 'gateway': True})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.location, service)

        # login - no service parameter
        self.app.reset()
        resp = self.app.post('/sso/login', params={
            'username': 'foo',
            'password': 'password',
            'submit': 'submit',
            'lt': 'abc'})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(
            resp.location, 'http://localhost/sso/login')
        self.assertIn('beaker.session.id', resp.headers.get('Set-Cookie'))

        # login - service parameter
        self.app.reset()
        resp = self.app.post(
            '/sso/login?%s' % service_qs, params={
                'username': 'foo',
                'password': 'password',
                'submit': 'submit',
                'lt': 'abc'})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.location), service)
        query = parse_qs(urlparse(resp.location).query)
        self.assertIn('ticket', query)
        self.assertTrue(TICKET_RE.match(query['ticket'][0]))

        # renew when logged in
        resp = self.app.get('/sso/login', params={'renew': True})
        self.assertEqual(resp.status_int, 200)

        # gateway request when logged in
        resp = self.app.get(
            '/sso/login', params={'service': service, 'gateway': True})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.location), service)
        query = parse_qs(urlparse(resp.location).query)
        self.assertIn('ticket', query)

        # normal get with service when logged in
        resp = self.app.get('/sso/login', params={'service': service})
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(clean_url(resp.location), service)
        query = parse_qs(urlparse(resp.location).query)
        self.assertIn('ticket', query)

        # normal get without service when logged in
        resp = self.app.get('/sso/login')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('You are signed in as foo', resp.body)

        # login with missing fields
        self.app.reset()
        resp = self.app.post('/sso/login', params={'submit': 'submit'})
        self.assertEqual(resp.status_int, 200)
        self.assertIn('Required', resp.body)

        # login with bad credentials
        resp = self.app.post(
            '/sso/login?%s' % service_qs, params={
                'username': 'foo',
                'password': 'password2',
                'submit': 'submit',
                'lt': 'abc'})
        self.assertEqual(resp.status_int, 200)
        self.assertIn('Username or password is incorrect', resp.body)

    def test_logout(self):
        service = 'http://example.com'
        user = self.create_user(self.db, username='foo', password='password')
        self.db.flush()
        [self.create_ticket(self.db, user_id=user.uuid, service=service)
         for i in range(10)]
        self.db.flush()

        resp = self.app.post(
            '/sso/login?%s' % urlencode({'service': service}), params={
                'username': 'foo',
                'password': 'password',
                'submit': 'submit',
                'lt': 'abc'})
        self.assertEqual(resp.status_int, 302)

        resp = self.app.get('/sso/logout')
        # logout consumes all tickets
        self.assertEqual(
            self.db.query(Ticket)
            .filter(Ticket.user == user)
            .filter(Ticket.consumed.is_(None))
            .count(), 0)
        self.assertEqual(
            self.db.query(Ticket)
            .filter(Ticket.user == user)
            .filter(Ticket.consumed.isnot(None))
            .count(), 11)
        # correct text is displayed
        self.assertIn('You have been signed out successfully', resp.body)

        # session is no longer authenticated
        with patch.object(CASViews, 'login_get') as mock_login_get, \
                patch.object(CASViews, '__init__') as mock_init:
            mock_login_get.return_value = {}
            mock_init.return_value = None
            self.app.get('/sso/login')
            self.assertNotIn('auth.userid', mock_init.call_args[0][0].session)

    def test_validate(self):
        app = self.create_app(self.db, title='Foo', password='password')
        user = self.create_user(self.db, username='foo', password='password')
        self.db.flush()
        auth_header = self.get_basic_auth_header(app.uuid, 'password')
        service = 'http://example.com'
        service_qs = urlencode({'service': service})

        resp = self.app.post(
            '/sso/login?%s' % service_qs, params={
                'username': 'foo',
                'password': 'password',
                'submit': 'submit',
                'lt': 'abc'})
        ticket_str = urlparse(resp.location).query
        ticket_str = parse_qs(ticket_str)['ticket'][0]
        ticket = self.db.query(Ticket) \
            .filter(Ticket.ticket == ticket_str) \
            .one()
        full_qs = urlencode({'ticket': ticket_str, 'service': service})

        # valid ticket + credentials
        resp = self.app.get('/sso/validate?%s' % full_qs, headers=auth_header)
        self.assertEqual(resp.json_body, {
            'uuid': user.uuid,
            'username': user.username,
            'app_data': {}})
        self.db.refresh(ticket)
        self.assertTrue(ticket.is_consumed)

        ticket_normal = self.create_ticket(
            self.db, service=service, user_id=user.uuid)
        ticket_consumed = self.create_ticket(
            self.db, service=service, user_id=user.uuid,
            consumed=datetime.utcnow())
        ticket_expired = self.create_ticket(
            self.db, service=service, user_id=user.uuid,
            expires=datetime.utcnow() - timedelta(seconds=1))
        ticket_primary = self.create_ticket(
            self.db, service=service, user_id=user.uuid,
            primary=True)
        self.db.flush()

        request_no_service = DummyRequest(
            params={'ticket': ticket_normal.ticket})
        request_no_ticket = DummyRequest(
            params={'service': service})
        request_cannot_renew = DummyRequest(
            params={'renew': True,
                    'service': service,
                    'ticket': ticket_normal.ticket})
        request_can_renew = DummyRequest(
            params={'renew': True,
                    'service': service,
                    'ticket': ticket_primary.ticket})
        request_diff_origin = DummyRequest(
            params={'service': 'http://domain.com',
                    'ticket': ticket_normal.ticket})
        request_invalid_str = DummyRequest(
            params={'service': service,
                    'ticket': 'im not a ticket string'})
        request_no_match = DummyRequest(
            params={'service': service,
                    'ticket': ticket_str})
        self.db.delete(ticket)
        self.db.flush()
        request_consumed = DummyRequest(
            params={'service': service,
                    'ticket': ticket_consumed.ticket})
        request_expired = DummyRequest(
            params={'service': service,
                    'ticket': ticket_expired.ticket})

        def assertValidateRaises(request, exception, msg=None):
            request.db = self.db
            ticket = self.db.query(Ticket) \
                .get(request.GET.get('ticket', ''))
            original_consumed = ticket.consumed if ticket else None

            if exception:
                with self.assertRaisesRegexp(exception, msg):
                    Ticket.validate(request)
            else:
                ticket = Ticket.validate(request)
                self.assertNotEqual(ticket.consumed, None)

            # reset the ticket
            if ticket:
                ticket.consumed = original_consumed
                self.db.flush()

        assertValidateRaises(request_no_service, InvalidRequest, 'No service')
        assertValidateRaises(request_no_ticket, InvalidTicket, 'No ticket')
        assertValidateRaises(
            request_cannot_renew, InvalidTicket, 'not issued via primary')
        assertValidateRaises(request_can_renew, None)
        assertValidateRaises(
            request_diff_origin, InvalidService, 'invalid for service')
        assertValidateRaises(
            request_invalid_str, InvalidTicket, r'Ticket string .* is invalid')
        assertValidateRaises(request_no_match, InvalidTicket, 'does not exist')
        assertValidateRaises(
            request_consumed, InvalidTicket, 'has already been used')
        assertValidateRaises(request_expired, InvalidTicket, 'has expired')

    def test_join(self):
        join_data = {
            'username': 'foo',
            'password': '1234',
            'csrf_token': 'abc',
            'submit': 'submit'
        }

        # normal get request to join view
        resp = self.app.get('/sso/join')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input type="text" name="username"', resp.body)
        self.assertIn('<input type="password" name="password"', resp.body)
        self.assertIn('<input type="hidden" name="csrf_token"', resp.body)

        # sign a user up
        resp = self.app.post('/sso/join', params=join_data)
        user = self.db.query(User).filter(User.username == 'foo').first()
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(
            resp.location, 'http://localhost/sso/login')
        self.assertTrue(user)
        self.assertEqual(user.password, '1234')
        self.assertEqual(user.app_data, {})

        # check that same username cannot sign up again
        resp = self.app.post('/sso/join', params=join_data)
        self.assertEqual(resp.status_int, 200)
        self.assertIn('foo is already taken', resp.body)
        self.assertIn('Please choose a different username', resp.body)

        # try to sign up user with otherwise invalid data
        join_data = join_data.copy()
        join_data['password'] = 'abcd'
        resp = self.app.post('/sso/join', params=join_data)
        self.assertEqual(resp.status_int, 200)
        self.assertIn('contains non-digit characters', resp.body)
