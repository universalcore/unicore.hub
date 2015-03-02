import os
import json
from urlparse import urljoin

import requests
from requests.auth import HTTPBasicAuth


class ClientException(Exception):
    pass


class BaseClient(object):

    def __init__(self, **settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(
            settings['app_id'],
            settings['app_password'])
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.host = settings['host']

    def _make_url(self, path):
        path = os.path.join(getattr(self, 'base_path', ''), path)
        return urljoin(self.host, path)

    def _request(self, method, path, *args, **kwargs):
        url = self._make_url(path)
        resp = self.session.request(method, url, *args, **kwargs)

        if resp.status_code not in (200, 201, 204):
            raise ClientException('HTTP %s: %s' %
                                  (resp.status_code, resp.content))

        return resp.json()

    def get(self, path, *args, **kwargs):
        return self._request('get', path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        kwargs['data'] = json.dumps(kwargs['data'])
        return self._request('post', path, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        kwargs['data'] = json.dumps(kwargs['data'])
        return self._request('put', path, *args, **kwargs)


class UserClient(BaseClient):
    base_path = '/users'

    def get_user(self, user_id):
        return self.get('%s' % user_id)

    def save_user(self, user_id, app_data):
        return self.post('%s' % user_id, data=app_data)
