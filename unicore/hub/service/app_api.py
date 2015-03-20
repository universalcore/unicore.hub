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
    uuid = request.matchdict['uuid']
    app = request.db.query(App).get(uuid)

    if app is None:
        raise NotFound

    return app


@resource(collection_path='/apps', path='/apps/{uuid}')
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

        self.request.db.flush()  # assigns primary key & key

        self.request.response.status_int = 201
        return app.to_dict()

    @view(renderer='json')
    def get(self):
        require_principal(
            self.request,
            ['group:apps_manager', self.request.matchdict['uuid']])

        app = get_app_object(self.request)
        return app.to_dict()

    @view(renderer='json')
    def put(self):
        require_principal(
            self.request,
            ['group:apps_manager', self.request.matchdict['uuid']])

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


app_key_reset = Service(
    name='apps-key-reset',
    path='/apps/{uuid}/reset_key',
    description='This service can be used by admin apps to '
                'reset an app\'s key')


@app_key_reset.put(renderer='json')
def reset_key(request):
    App.get_authenticated_object(request)
    require_principal(
        request, ['group:apps_manager', request.matchdict['uuid']])

    app = get_app_object(request)
    app.key = utils.make_key()

    return app.to_dict()
