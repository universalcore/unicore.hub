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
    path='/apps/{app_id}',
    description='This service can be used by admin apps to '
                'retrieve and update app data')
app_password_reset = Service(
    name='apps-password-reset',
    path='/apps/{app_id/reset_password',
    description='This service can be used by admin apps to '
                'reset an app\'s password'
    )


def get_app_object(request):
    app_id = request.matchdict['app_id']
    app = request.db.query(App).get(app_id)

    if app is None:
        raise NotFound

    return app


@app_creation.post(permission='create_app')
def create_app(request):
    app = get_app_object(request)
    valid_data = AppSchema().deserialize(request.json_body)
    for attr, value in valid_data.iteritems():
        setattr(app, attr, value)

    password = utils.make_password(bit_length=15)
    app.password = password
    request.db.flush()  # assigns primary key + slug

    new_data = app.to_dict()
    # the password cannot be retrieved after creation
    new_data['password'] = password
    return new_data


@app_management.get(permission='view_app')
def view_app(request):
    app = get_app_object(request)
    return app.to_dict()


@app_management.put(permission='edit_app')
def edit_app(request):
    app = get_app_object(request)
    valid_data = AppSchema().deserialize(request.json_body)

    # changing groups requires manager permissions
    groups = valid_data.pop('groups', app.groups)
    if 'group:apps_manager' in request.effective_principals:
        app.groups = groups
    elif groups != app.groups:
        raise Forbidden

    for attr, value in valid_data.iteritems():
        setattr(app, attr, value)

    return app.to_dict()


@app_password_reset.put(permission='edit_app')
def reset_password(request):
    app = get_app_object(request)
    password = utils.make_password(bit_length=15)
    app.password = password

    new_data = app.to_dict()
    # the password cannot be retrieved after creation
    new_data['password'] = password
    return new_data
