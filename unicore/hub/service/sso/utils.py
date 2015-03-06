from urlparse import urljoin
from urllib import urlencode

from pyramid.httpexceptions import HTTPFound


def make_ticket(service, user_id):
    return 'this_is_a_ticket'  # TODO: need to store tickets


def make_redirect(service=None, route_name=None, request=None, params={}):
    if service:
        location = urljoin(service, '?%s' % urlencode(params))
        return HTTPFound(location=location)
    return HTTPFound(request.route_url(route_name))


if __name__ == '__main__':
    assert make_redirect('http://domain.com/', {'param1': '1'}).location \
        == 'http://domain.com/?param1=1'
    from uuid import uuid4
    user_id = uuid4().hex
    assert make_ticket('http://domain.com/', user_id) == 'this_is_a_ticket'
