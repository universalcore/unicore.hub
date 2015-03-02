import json
from unittest import TestCase
from urlparse import urljoin

import responses
import requests
from requests.auth import HTTPBasicAuth

from unicore.hub.client import UserClient, ClientException


class UserClientTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app_id = 5678
        cls.app_password = 'dakfjd042342cs'
        cls.host = 'http://localhost:8000'
        cls.client = UserClient(
            app_id=cls.app_id,
            app_password=cls.app_password,
            host=cls.host
        )

    @responses.activate
    def test_get_user(self):
        user_id = 1234
        user_app_data = {'display_name': 'foo'}
        url = urljoin(self.host, '/users/%s' % user_id)
        responses.add(
            responses.GET, url,
            body=json.dumps(user_app_data),
            status=200,
            content_type='application/json'
        )

        data = self.client.get_user(user_id)
        self.assertEqual(data, user_app_data)
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertEqual(request.url, url)
        basic_auth = HTTPBasicAuth(self.app_id, self.app_password)
        request_with_auth = basic_auth(requests.Request())
        self.assertEqual(request.headers['Authorization'],
                         request_with_auth.headers['Authorization'])

        responses.reset()
        responses.add(responses.GET, url, status=404)
        with self.assertRaises(ClientException):
            self.client.get_user(user_id)

    @responses.activate
    def test_save_user(self):
        user_id = 1234
        user_app_data = {'display_name': 'foo'}
        url = urljoin(self.host, '/users/%s' % user_id)
        responses.add(
            responses.POST, url,
            body=json.dumps(user_app_data),
            status=200,
            content_type='application/json'
        )

        data = self.client.save_user(user_id, user_app_data)
        self.assertEqual(data, user_app_data)
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertEqual(request.url, url)
        basic_auth = HTTPBasicAuth(self.app_id, self.app_password)
        request_with_auth = basic_auth(requests.Request())
        self.assertEqual(request.headers['Authorization'],
                         request_with_auth.headers['Authorization'])

        responses.reset()
        responses.add(responses.POST, url, status=404)
        with self.assertRaises(ClientException):
            self.client.save_user(user_id, {})
