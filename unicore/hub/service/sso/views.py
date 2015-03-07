from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember

import colander
from deform import Form, ValidationFailure
from deform.widget import PasswordWidget

from unicore.hub.service.models import User
from unicore.hub.service.sso.utils import (make_redirect,
                                           make_ticket_and_redirect)


""" Using django-mama-cas as the reference implementation
https://github.com/jbittel/django-mama-cas/blob/master/mama_cas/views.py
"""


class UserCredentials(colander.MappingSchema):
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        widget=PasswordWidget(length=4))


def validate_credentials(request):

    def validator(form, values):
        user_id = User.authenticate(
            values['username'], values['password'], request)
        if not user_id:
            raise colander.Invalid(form, 'Username or password is incorrect')
        values['user_id'] = user_id

    return validator


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
        schema = UserCredentials()
        form = Form(schema, buttons=('submit', ))

        if renew:
            return {'form': form.render()}

        user_id = self.request.authenticated_userid

        if gateway and service:
            if user_id:
                return make_ticket_and_redirect(service, user_id)
            return make_redirect(service)

        if user_id:
            if service:
                return make_ticket_and_redirect(service, user_id)
            return {'user': self.request.db.query(User).get(user_id)}

        return {'form': form.render()}

    @view_config(
        route_name='user-login', request_method='POST',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_post(self):
        service = self.request.matchdict.get('service', None)
        schema = UserCredentials(validator=validate_credentials(self.request))
        form = Form(schema, buttons=('submit', ))

        if 'submit' in self.request.POST:
            data = self.request.POST.items()

            try:
                data = form.validate(data)
                user_id = data['user_id']
                remember(self.request, user_id)
                if service:
                    return make_ticket_and_redirect(service, user_id)
                return make_redirect(
                    route_name='user-login', request=self.request)

            except ValidationFailure as e:
                return {'form': e.render()}

        return {'form': form.render()}

    @view_config(route_name='user-logout')
    def logout(self):
        service = self.request.matchdict.get('service', None)
        forget(self.request)

        if service:
            return make_redirect(service)

        return make_redirect(route_name='user-login', request=self.request)

    @view_config(route_name='user-validate', renderer='text')
    def validate(self):
        # service = self.request.matchdict.get('service', None)
        # ticket = self.request.matchdict.get('ticket', None)
        # renew = bool(self.request.matchdict.get('renew', False))

        # TODO: validate ticket
        pass
