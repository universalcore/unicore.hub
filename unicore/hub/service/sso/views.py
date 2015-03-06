from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember

from unicore.hub.service.models import User
from unicore.hub.service.sso.utils import (make_ticket,
                                           make_redirect)


""" Using django-mama-cas as the reference implementation
https://github.com/jbittel/django-mama-cas/blob/master/mama_cas/views.py
"""


@view_defaults(http_cache=0, request_method='GET')
class CASViews(object):

    def __init__(self, request):
        self.request = request

    # TODO: csrf check
    @view_config(
        route_name='user-login',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_get(self):
        service = self.request.matchdict.get('service', None)
        renew = bool(self.request.matchdict.get('renew', False))
        gateway = bool(self.request.matchdict.get('gateway', False))

        if renew:
            return {}

        user_id = self.request.authenticated_userid

        if gateway and service:
            if user_id:
                ticket = make_ticket(service=service, user_id=user_id)
                return make_redirect(service, params={'ticket': ticket})
            return make_redirect(service)

        if user_id:
            if service:
                ticket = make_ticket(service=service, user_id=user_id)
                return make_redirect(service, params={'ticket': ticket})
            return {'user': self.request.db.query(User).get(user_id)}

        return {}

    @view_config(
        route_name='user-login', request_method='POST',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_post(self):
        service = self.request.matchdict.get('service', None)

        if service:
            pass  # TODO: form handling

        return make_redirect(route_name='user-login', request=self.request)

    @view_config(route_name='user-logout')
    def logout(self):
        service = self.request.matchdict.get('service', None)
        forget(self.request)

        if service:
            return make_redirect(service)

        return make_redirect(route_name='user-login', request=self.request)

    @view_config(
        route_name='user-validate', renderer='text')
    def validate(self):
        service = self.request.matchdict.get('service', None)
        ticket = self.request.matchdict.get('ticket', None)
        renew = bool(self.request.matchdict.get('renew', False))

        # TODO: validate ticket
