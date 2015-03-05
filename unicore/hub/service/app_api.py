from pyramid.exceptions import NotFound, Forbidden

from cornice import Service

from unicore.hub.service.models import App
from unicore.hub.service.schema import App as AppSchema
from unicore.hub.service import utils


app_creation = Service(
    name='apps-create',
    path='/apps',
    description='This service can be used by admin apps to '
                'create new apps')
app_management = Service(
    name='apps',
    path='/apps/{app_id:\d+}',
    description='This service can be used by admin apps to '
                'retrieve and update app data')
app_password_reset = Service(
    name='apps-password-reset',
    path='/apps/{app_id:\d+}/reset_password',
    description='This service can be used by admin apps to '
                'reset an app\'s password')


def get_app_object(request):
    app_id = request.matchdict['app_id']
    app = request.db.query(App).get(app_id)

    if app is None:
        raise NotFound

    return app


def require_principal(request, principals):
    App.get_authenticated_object(request)

    effective_principals = set(request.effective_principals)
    accepted_principals = set(principals)
    if not effective_principals.intersection(accepted_principals):
        raise Forbidden


@app_creation.post()
def create_app(request):
    require_principal(request, ['group:apps_manager'])

    app = App()
    request.db.add(app)
    valid_data = AppSchema().deserialize(request.json_body)
    for attr, value in valid_data.iteritems():
        setattr(app, attr, value)

    password = utils.make_password(bit_length=15)
    app.password = password
    request.db.flush()  # assigns primary key + slug

    new_data = app.to_dict()
    # the password cannot be retrieved after creation
    new_data['password'] = password
    request.response.status_int = 201
    return new_data


@app_management.get()
def view_app(request):
    require_principal(
        request, ['group:apps_manager', int(request.matchdict['app_id'])])

    app = get_app_object(request)
    return app.to_dict()


@app_management.put()
def edit_app(request):
    require_principal(
        request, ['group:apps_manager', int(request.matchdict['app_id'])])

    app = get_app_object(request)
    valid_data = AppSchema().deserialize(request.json_body)

    # changing groups requires manager permissions
    app_groups = app.groups or []
    groups = valid_data.pop('groups', app_groups)
    if 'group:apps_manager' in request.effective_principals:
        app.groups = groups
    elif groups != app_groups:
        raise Forbidden

    for attr, value in valid_data.iteritems():
        setattr(app, attr, value)

    return app.to_dict()


@app_password_reset.put()
def reset_password(request):
    require_principal(
        request, ['group:apps_manager', int(request.matchdict['app_id'])])

    app = get_app_object(request)
    password = utils.make_password(bit_length=15)
    app.password = password

    new_data = app.to_dict()
    # the password cannot be retrieved after creation
    new_data['password'] = password
    return new_data
