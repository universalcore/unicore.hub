from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPUnauthorized

from cornice import Service

from unicore.hub.service.models import App, User


user_app_data = Service(
    name='users',
    path='/users/{user_id}',
    description='This service can be used to retrieve '
                'and update user data on a per app basis')


def get_authenticated_app_object(request):
    try:
        [app_id] = request.authenticated_userid
    except TypeError:
        raise HTTPUnauthorized()

    return request.db.query(App).get(app_id)


def get_user_object(request):
    user_id = request.matchdict['user_id']
    user = request.db.query(User).get(user_id)

    if user is None:
        raise NotFound

    return user


@user_app_data.get()
def get_user(request):
    app = get_authenticated_app_object(request)
    user = get_user_object(request)
    return (user.app_data or {}).get(app.id, {})


@user_app_data.post()
def save_user(request):
    app = get_authenticated_app_object(request)
    user = get_user_object(request)
    app_data = user.app_data

    if isinstance(app_data, dict):
        app_data[app.id] = request.json_body
    else:
        app_data = {app.id: request.json_body}
    user.app_data = app_data

    return {'success': True}
