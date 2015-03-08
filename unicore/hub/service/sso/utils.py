from urlparse import urljoin, urlparse
from urllib import urlencode

from pyramid.httpexceptions import HTTPFound


PROTOCOL_TO_PORT = {
    'http': 80,
    'https': 443,
}


def same_origin(url1, url2):
    ''' Copied from Django
    https://github.com/django/django/blob/master/django/utils/http.py#L255
    '''
    p1, p2 = urlparse(url1), urlparse(url2)
    try:
        o1 = (p1.scheme, p1.hostname, p1.port or PROTOCOL_TO_PORT[p1.scheme])
        o2 = (p2.scheme, p2.hostname, p2.port or PROTOCOL_TO_PORT[p2.scheme])
        return o1 == o2
    except (ValueError, KeyError):
        return False


def make_redirect(service=None, route_name=None, request=None, params={}):
    if service:
        location = urljoin(service, '?%s' % urlencode(params))
        return HTTPFound(location=location)
    return HTTPFound(request.route_url(route_name))
