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
    [slug] = (request.authenticated_userid, )
    if slug is None:
        raise HTTPUnauthorized()

    return request.db.query(App) \
        .filter(App.slug == slug) \
        .one()


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
    app_data = user.app_data or {}
    key = app.slug
    return app_data.get(key, {})


@user_app_data.post()
def save_user(request):
    app = get_authenticated_app_object(request)
    user = get_user_object(request)

    key = app.slug
    if isinstance(user.app_data, dict):
        user.app_data[key] = request.json_body
    else:
        user.app_data = {key: request.json_body}

    return {'success': True}
