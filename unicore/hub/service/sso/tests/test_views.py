from unicore.hub.service.tests import DBTestCase


class CASViewsTestCase(DBTestCase):

    def test_locale(self):
        resp = self.app.get('/sso/login')
        self.assertIn('Set-Cookie', resp.headers)
        self.assertIn('_LOCALE_=eng_GB', resp.headers['Set-Cookie'])

        resp = self.app.get('/sso/login')
        self.assertNotIn('Set-Cookie', resp.headers)

        resp = self.app.get('/sso/login?_LOCALE_=tam_IN')
        self.assertIn('Set-Cookie', resp.headers)
        self.assertIn('_LOCALE_=tam_IN', resp.headers['Set-Cookie'])
