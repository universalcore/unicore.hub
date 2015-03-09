from urllib import urlencode
from urlparse import urljoin

from pyramid.view import view_config, view_defaults
from pyramid.security import forget, remember
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory, get_locale_name

import colander
from deform import Form, ValidationFailure
from deform.widget import PasswordWidget

from unicore.hub.service.models import User
from unicore.hub.service.sso.models import Ticket, TicketValidationError


_ = TranslationStringFactory(None)
# known Right to Left language codes
KNOWN_RTL = set(["urd", "ara", "arc", "per", "heb", "kur", "yid"])


class UserCredentials(colander.MappingSchema):
    username = colander.SchemaNode(
        colander.String(),
        title=_('Username'))
    password = colander.SchemaNode(
        colander.String(),
        widget=PasswordWidget(length=4),
        title=_('Password'))


def validate_credentials(request):

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
        cookies = filter(
            lambda t: t[0] == 'Set-Cookie',
            self.request.response.headerlist)

        if url:
            location = urljoin(url, '?%s' % urlencode(params))
        else:
            location = self.request.route_url(route_name)

        resp = HTTPFound(location, headers=cookies)
        return resp


@view_defaults(http_cache=0, request_method='GET')
class CASViews(BaseView):

    # TODO: csrf check
    @view_config(
        route_name='user-login',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_get(self):
        service = self.request.GET.get('service', None)
        renew = bool(self.request.GET.get('renew', False))
        gateway = bool(self.request.GET.get('gateway', False))
        schema = UserCredentials()
        form = Form(schema, buttons=('submit', ))

        if renew:
            return {'form': form.render()}

        user_id = self.request.authenticated_userid

        if gateway and service:
            if user_id:
                ticket = Ticket.create_ticket_from_request(self.request)
                return self.make_redirect(
                    service, params={'ticket': ticket.ticket})
            return self.make_redirect(service)

        if user_id:
            if service:
                ticket = Ticket.create_ticket_from_request(self.request)
                return self.make_redirect(
                    service, params={'ticket': ticket.ticket})
            return {'user': self.request.db.query(User).get(user_id)}

        return {'form': form.render()}

    @view_config(
        route_name='user-login', request_method='POST',
        renderer='unicore.hub:service/sso/templates/login.jinja2')
    def login_post(self):
        service = self.request.GET.get('service', None)
        schema = UserCredentials(validator=validate_credentials(self.request))
        form = Form(schema, buttons=('submit', ))

        if 'submit' in self.request.POST:
            data = self.request.POST.items()

            try:
                data = form.validate(data)
                user_id = data['user_id']
                headers = remember(self.request, (user_id, ))
                self.request.response.headerlist.extend(headers)
                if service:
                    ticket = Ticket.create_ticket_from_request(
                        self.request, user_id=user_id, primary=True)
                    return self.make_redirect(
                        service, params={'ticket': ticket.ticket})
                return self.make_redirect(route_name='user-login')

            except ValidationFailure as e:
                return {'form': e.render()}

        return {'form': form.render()}

    @view_config(route_name='user-logout')
    def logout(self):
        service = self.request.GET.get('service', None)
        headers = forget(self.request)
        self.request.response.headerlist.extend(headers)

        if service:
            return self.make_redirect(service)

        return self.make_redirect(route_name='user-login')

    @view_config(route_name='user-validate', renderer='json')
    def validate(self):
        try:
            # NOTE: this view's authenticated user is an app
            # unlike the login and logout views
            [app_id] = self.request.authenticated_userid
            ticket = Ticket.validate(self.request)
            # CAS 1.0 says to return 'yes\n' but this way we avoid
            # an unnecessary request to obtain user data
            data = ticket.user.to_dict()
            data['app_data'] = (data['app_data'] or {}).get(app_id, {})

        except (TicketValidationError, TypeError):
            data = "no\n"

        return data
