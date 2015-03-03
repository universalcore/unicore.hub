from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import Allow
from sqlalchemy import Column, Integer, Unicode
from sqlalchemy_utils import PasswordType, JSONType, ScalarListType
from sqlalchemy.ext.mutable import MutableDict

from unicore.hub.service import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255), unique=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))
    app_data = Column(MutableDict.as_mutable(JSONType))

    @classmethod
    def authenticate(cls, username, password, request):
        user = request.db.query(cls) \
            .filter(cls.username == username) \
            .first()

        if user is not None and user.password == password:
            return (user.id, )

        return None


class App(Base):
    __tablename__ = 'apps'

    # TODO - extend to cover user api
    all_groups = (
        'group:apps_manager',  # Can create, view and edit apps
    )
    permissions_basic = ['view_app', 'edit_app']
    permissions_advanced = ['create_app']

    id = Column(Integer, primary_key=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))
    groups = Column(ScalarListType())

    @classmethod
    def authenticate(cls, app_id, password, request):
        app = request.db.query(cls).get(app_id)

        if app is not None and app.password == password:
            return [app_id, ] + app.all_groups

        return None

    @classmethod
    def get_authenticated_object(cls, request):
        try:
            [app_id] = request.authenticated_userid
        except TypeError:
            raise HTTPUnauthorized()

        return request.db.query(cls).get(app_id)

    def __acl__(self):
        return [
            (Allow, self.id, App.permissions_basic),
            (Allow, 'group:apps_manager',
                App.permissions_basic + App.permissions_advanced)
        ]
