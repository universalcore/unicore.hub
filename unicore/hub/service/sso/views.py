from urllib import urlencode
from urlparse import urljoin

from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember
from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized, HTTPBadRequest
from pyramid.i18n import get_locale_name

import colander
from deform import Form, ValidationFailure
from deform.widget import PasswordWidget, HiddenWidget

from unicore.hub.service.models import User, App
from unicore.hub.service.schema import User as UserSchema
from unicore.hub.service.validators import pin_validator
from unicore.hub.service.utils import (normalize_unicode,
                                       translation_string_factory as _)
from unicore.hub.service.sso.models import Ticket, TicketValidationError
from unicore.hub.service.sso.utils import deferred_csrf_default, \
    deferred_csrf_validator, InvalidCSRFToken


# known Right to Left language codes
KNOWN_RTL = set(["urd", "ara", "arc", "per", "heb", "kur", "yid"])


class UserCredentials(colander.MappingSchema):
    # NOTE: the name of the csrf token is 'lt' as per CAS 1.0
    lt = colander.SchemaNode(
        colander.String(),
        default=deferred_csrf_default,
        widget=HiddenWidget(),
        validator=deferred_csrf_validator)
    username = colander.SchemaNode(
        colander.String(),
        preparer=normalize_unicode,
        title=_('Username'))
    password = colander.SchemaNode(
        colander.String(),
        widget=PasswordWidget(length=4),
        title=_('Password'))


class UserJoin(UserSchema):
    csrf_token = colander.SchemaNode(
        colander.String(),
        default=deferred_csrf_default,
        widget=HiddenWidget(),
        validator=deferred_csrf_validator)
    password = colander.SchemaNode(
        colander.String(),
        widget=PasswordWidget(length=4),
        validator=pin_validator(length=4))


@colander.deferred
def validate_credentials(node, kw):
    request = kw.get('request')

    def validator(form, values):
        user_id = User.authenticate(
            values['username'], values['password'], request)
        if not user_id:
            raise colander.Invalid(
                form, _('Username or password is incorrect'))
        values['user_id'] = user_id[0]

    return validator


class BaseView(object):

    def __init__(self, request):
        self.request = request
        self.locale = get_locale_name(request)
        if request.cookies.get('_LOCALE_', None) != self.locale:
            request.response.set_cookie(
                '_LOCALE_', value=self.locale, max_age=31536000)

        self.request.tmpl_context.language_direction = \
            self.get_language_direction()

    def get_language_direction(self):
        language_code, _, country_code = self.locale.partition('_')
        if language_code in KNOWN_RTL:
            return "rtl"
        else:
            return "ltr"

    def make_redirect(self, url=None, route_name=None, params={}):
        # TODO: validate url
        # TODO: preserve service, renew and gateway query params
        cookies = filter(
            lambda t: t[0] == 'Set-Cookie',
            self.request.response.headerlist)

        if url:
            location = urljoin(url, '?%s' % urlencode(params))
        else:
            location = self.request.route_path(
                route_name, _query=self.request.query_string)

        resp = HTTPFound(location, headers=cookies)
        return resp


@view_defaults(http_cache=0, request_method='GET')
class CASViews(BaseView):

    @view_config(
        route_name='user-login',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_get(self):
        service = self.request.GET.get('service', None)
        renew = bool(self.request.GET.get('renew', False))
        gateway = bool(self.request.GET.get('gateway', False))
        schema = UserCredentials().bind(request=self.request)
        form = Form(schema, buttons=('submit', ))

        if renew:
            return {'form': form}

        try:
            user = User.get_authenticated_object(self.request)
        except HTTPUnauthorized:
            user = None

        if gateway and service:
            if user:
                ticket = Ticket.create_ticket_from_request(self.request)
                return self.make_redirect(
                    service, params={'ticket': ticket.ticket})
            return self.make_redirect(service)

        if user:
            if service:
                ticket = Ticket.create_ticket_from_request(self.request)
                return self.make_redirect(
                    service, params={'ticket': ticket.ticket})
            return {'user': user}

        return {'form': form}

    @view_config(
        route_name='user-login', request_method='POST',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_post(self):
        if 'submit' not in self.request.POST:
            schema = UserCredentials().bind(request=self.request)
            return {'form': Form(schema, buttons=('submit', ))}

        service = self.request.GET.get('service', None)
        schema = UserCredentials(validator=validate_credentials) \
            .bind(request=self.request, use_existing_csrf=True)
        form = Form(schema, buttons=('submit', ))
        data = self.request.POST.items()

        try:
            data = form.validate(data)
            # NB: invalidate the old CSRF token
            # CAS 1.0 requires new CSRF token per request
            self.request.session.new_csrf_token()
            user_id = data['user_id']
            headers = remember(self.request, user_id)
            self.request.response.headerlist.extend(headers)
            if service:
                ticket = Ticket.create_ticket_from_request(
                    self.request, user_id=user_id, primary=True)
                return self.make_redirect(
                    service, params={'ticket': ticket.ticket})
            return self.make_redirect(route_name='user-login')

        except ValidationFailure as e:
            # NB: invalidate the old CSRF token
            # CAS 1.0 requires new CSRF token per request
            e.field['lt']._cstruct = self.request.session.new_csrf_token()
            return {'form': e.field}

        except InvalidCSRFToken:
            # CSRF check failed
            raise HTTPBadRequest

    @view_config(
        route_name='user-logout',
        renderer='unicore.hub:service/sso/templates/logout_success.jinja2')
    def logout(self):
        try:
            user = User.get_authenticated_object(self.request)
            Ticket.consume_all(user, self.request)
        except HTTPUnauthorized:
            pass

        headers = forget(self.request)
        self.request.response.headerlist.extend(headers)

        return {}

    @view_config(route_name='user-validate', renderer='json')
    def validate(self):
        try:
            # NOTE: this view's authenticated user is an app
            # unlike the login and logout views
            app = App.get_authenticated_object(self.request)
            ticket = Ticket.validate(self.request)
            # CAS 1.0 says to return 'yes\n' but this way we avoid
            # an unnecessary request to obtain user data
            data = ticket.user.to_dict()
            data['app_data'] = (data['app_data'] or {}).get(app.uuid, {})

        except (TicketValidationError, HTTPUnauthorized):
            data = "no\n"

        return data

    @view_config(
        route_name='user-join',
        renderer='unicore.hub:service/sso/templates/join.jinja2')
    def join_get(self):
        schema = UserJoin().bind(request=self.request)
        form = Form(schema, buttons=('submit', ))

        return {'form': form}

    @view_config(
        route_name='user-join',
        renderer='unicore.hub:service/sso/templates/join.jinja2',
        request_method='POST')
    def join_post(self):
        if 'submit' not in self.request.POST:
            schema = UserJoin().bind(request=self.request)
            return {'form': Form(schema, buttons=('submit', ))}

        schema = UserJoin().bind(request=self.request, use_existing_csrf=True)
        form = Form(schema, buttons=('submit', ))
        data = self.request.POST.items()

        try:
            data = form.validate(data)
            # NB: invalidate the old CSRF token
            # CAS 1.0 requires new CSRF token per request
            self.request.session.new_csrf_token()
            # create new user
            user = User()
            self.request.db.add(user)
            del data['csrf_token']
            for attr, value in data.iteritems():
                setattr(user, attr, value)
            self.request.db.flush()

            headers = remember(self.request, user.uuid)
            self.request.response.headerlist.extend(headers)
            return self.make_redirect(route_name='user-login')

        except ValidationFailure as e:
            # NB: invalidate the old CSRF token
            # CAS 1.0 requires new CSRF token per request
            e.field['csrf_token']._cstruct = (
                self.request.session.new_csrf_token())
            return {'form': e.field}

        except InvalidCSRFToken:
            # CSRF check failed
            raise HTTPBadRequest
