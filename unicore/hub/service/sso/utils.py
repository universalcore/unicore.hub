from uuid import uuid4
from urlparse import urlparse, urlunparse

import colander

from unicore.google.tasks import pageview


PROTOCOL_TO_PORT = {
    'http': 80,
    'https': 443,
}
ONE_YEAR = 31556952


def same_origin(url1, url2):
    ''' Return True if the urls have the same origin, else False.
    Copied from Django:
    https://github.com/django/django/blob/master/django/utils/http.py#L255
    '''
    p1, p2 = urlparse(url1), urlparse(url2)
    try:
        o1 = (p1.scheme, p1.hostname, p1.port or PROTOCOL_TO_PORT[p1.scheme])
        o2 = (p2.scheme, p2.hostname, p2.port or PROTOCOL_TO_PORT[p2.scheme])
        return o1 == o2
    except (ValueError, KeyError):
        return False


def clean_url(url):
    """ Return only scheme, host and path
    """
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, parts.path, '', '', ''))


class InvalidCSRFToken(ValueError):
    pass


@colander.deferred
def deferred_csrf_default(node, kw):
    request = kw.get('request')
    if kw.get('use_existing_csrf', False):
        csrf_token = request.session.get_csrf_token()
    else:
        csrf_token = request.session.new_csrf_token()
    return csrf_token


@colander.deferred
def deferred_csrf_validator(node, kw):

    def validator(node, value):
        request = kw.get('request')
        csrf_token = request.session.get_csrf_token()
        if value != csrf_token:
            raise InvalidCSRFToken('Bad CSRF token')

    return validator


def track_ga_pageview(request):
    profile_id = request.registry.settings.get('ga.profile_id')
    if not profile_id:
        return

    client_id = request.cookies.get('ga_client_id', uuid4().hex)
    request.response.set_cookie(
        'ga_client_id', value=client_id, max_age=ONE_YEAR)

    data = {
        'path': request.path,
        'uip': request.remote_addr,
        'dr': request.referer or '',
        'dh': request.domain,
        'user_agent': request.user_agent,
        'ul': unicode(request.accept_language)}

    if request.authenticated_userid:
        [data['uid']] = request.authenticated_userid

    pageview.delay(profile_id, client_id, data)
