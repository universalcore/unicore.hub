from pyramid.view import view_config, view_defaults


""" Using django-mama-cas as the reference implementation
https://github.com/jbittel/django-mama-cas/blob/master/mama_cas/views.py
"""


@view_defaults(http_cache=0, request_method='GET')
class CASViews(object):

    def __init__(self, request):
        self.request = request

    @view_config(
        route_name='user-login', request_method=('GET', 'POST'),
        renderer='unicore.hub:hub/service/sso/templates/login.jinja2',
        check_csrf=True)
    def login(self):
        return {}

    @view_config(
        route_name='user-logout',
        renderer='unicore.hub:hub/service/sso/templates/logout.jinja2')
    def logout(self):
        return {}

    @view_config(
        route_name='user-validate', renderer='json')
    def validate(self):
        return {}
