from unittest import TestCase

import mock
from zope.interface import implementer

from pyramid import testing
from pyramid.interfaces import IAuthenticationPolicy

from unicore.hub.service.sso.utils import track_ga_pageview


class GATestCase(TestCase):
    default_data = {
        'path': '/',
        'remote_addr': '127.0.0.1',
        'referer': 'http://localhost:8080/',
        'domain': 'hub.unicore.io',
        'user_agent': 'dummy agent',
        'accept_language': 'fr'}

    def make_request(self, **overrides):
        data = self.default_data.copy()
        data.update(overrides)
        return testing.DummyRequest(**data)

    @mock.patch('unicore.hub.service.sso.utils.pageview.delay')
    def test_no_ga_profile_id(self, mock_pageview_task):
        request = self.make_request()
        request.registry.settings = {}

        track_ga_pageview(request)
        mock_pageview_task.assert_not_called()

    @mock.patch('unicore.hub.service.sso.utils.pageview.delay')
    @mock.patch('unicore.hub.service.sso.utils.uuid4')
    def test_track_pageview(self, mock_uuid, mock_pageview_task):
        request = self.make_request()
        request.registry.settings = {'ga.profile_id': '1234'}
        mock_uuid.return_value = mock.Mock()
        mock_uuid.return_value.hex = 'imarandomuuid'

        # no authenticated user or client_id
        track_ga_pageview(request)
        mock_pageview_task.assert_called_with(
            '1234', 'imarandomuuid', {
                'path': self.default_data['path'],
                'uip': self.default_data['remote_addr'],
                'dr': self.default_data['referer'],
                'dh': self.default_data['domain'],
                'user_agent': self.default_data['user_agent'],
                'ul': self.default_data['accept_language']})

        # with authenticated user and existing client_id
        request = self.make_request(cookies={'ga_client_id': 'imaclientid'})

        @implementer(IAuthenticationPolicy)
        class DummyAuth(object):
            def authenticated_userid(self, request):
                return ('imauseruuid', )

        request.registry.registerUtility(DummyAuth())
        track_ga_pageview(request)
        mock_pageview_task.assert_called_with(
            '1234', 'imaclientid', {
                'path': self.default_data['path'],
                'uip': self.default_data['remote_addr'],
                'dr': self.default_data['referer'],
                'dh': self.default_data['domain'],
                'user_agent': self.default_data['user_agent'],
                'ul': self.default_data['accept_language'],
                'uid': 'imauseruuid'})
