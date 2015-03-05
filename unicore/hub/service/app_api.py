from pyramid.exceptions import NotFound, Forbidden

from cornice import Service
from cornice.resource import resource, view

from unicore.hub.service.models import App
from unicore.hub.service.schema import App as AppSchema
from unicore.hub.service import utils


def require_principal(request, principals):
    effective_principals = set(request.effective_principals)
    accepted_principals = set(principals)
    if not effective_principals.intersection(accepted_principals):
        raise Forbidden


def get_app_object(request):
    app_id = request.matchdict['app_id']
    app = request.db.query(App).get(app_id)

    if app is None:
        raise NotFound

    return app


@resource(collection_path='/apps', path='/apps/{app_id:\d+}')
class AppResource(object):

    def __init__(self, request):
        self.admin_app = App.get_authenticated_object(request)
        self.request = request

    @view(renderer='json')
    def collection_post(self):
        require_principal(self.request, ['group:apps_manager'])

        app = App()
        self.request.db.add(app)
        valid_data = AppSchema().deserialize(self.request.json_body)
        for attr, value in valid_data.iteritems():
            setattr(app, attr, value)

        password = utils.make_password(bit_length=15)
        app.password = password
        self.request.db.flush()  # assigns primary key + slug

        new_data = app.to_dict()
        # the password cannot be retrieved after creation
        new_data['password'] = password
        self.request.response.status_int = 201
        return new_data

    @view(renderer='json')
    def get(self):
        require_principal(
            self.request,
            ['group:apps_manager', int(self.request.matchdict['app_id'])])

        app = get_app_object(self.request)
        return app.to_dict()

    @view(renderer='json')
    def put(self):
        require_principal(
            self.request,
            ['group:apps_manager', int(self.request.matchdict['app_id'])])

        app = get_app_object(self.request)
        valid_data = AppSchema().deserialize(self.request.json_body)

        # changing groups requires manager permissions
        app_groups = app.groups or []
        groups = valid_data.pop('groups', app_groups)
        if 'group:apps_manager' in self.request.effective_principals:
            app.groups = groups
        elif groups != app_groups:
            raise Forbidden

        for attr, value in valid_data.iteritems():
            setattr(app, attr, value)

        return app.to_dict()


app_password_reset = Service(
    name='apps-password-reset',
    path='/apps/{app_id:\d+}/reset_password',
    description='This service can be used by admin apps to '
                'reset an app\'s password')


@app_password_reset.put(renderer='json')
def reset_password(request):
    App.get_authenticated_object(request)
    require_principal(
        request, ['group:apps_manager', int(request.matchdict['app_id'])])

    app = get_app_object(request)
    password = utils.make_password(bit_length=15)
    app.password = password

    new_data = app.to_dict()
    # the password cannot be retrieved after creation
    new_data['password'] = password
    return new_data
