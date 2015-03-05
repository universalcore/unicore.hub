from pyramid.exceptions import NotFound

from cornice import Service

from unicore.hub.service.models import App, User


user_app_data = Service(
    name='users',
    path='/users/{user_id}',
    description='This service can be used to retrieve '
                'and update user data on a per app basis')


def get_user_object(request):
    user_id = request.matchdict['user_id']
    user = request.db.query(User).get(user_id)

    if user is None:
        raise NotFound

    return user


@user_app_data.get()
def get_user(request):
    app = App.get_authenticated_object(request)
    user = get_user_object(request)
    app_data = user.app_data or {}
    key = app.slug
    return app_data.get(key, {})


@user_app_data.post()  # TODO: this should be PUT
def save_user(request):
    app = App.get_authenticated_object(request)
    user = get_user_object(request)

    key = app.slug
    if isinstance(user.app_data, dict):
        user.app_data[key] = request.json_body
    else:
        user.app_data = {key: request.json_body}

    return {'success': True}
