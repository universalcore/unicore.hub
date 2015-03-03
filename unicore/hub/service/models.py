from pyramid.httpexceptions import HTTPUnauthorized
from sqlalchemy import Column, Integer, Unicode
from sqlalchemy_utils import PasswordType, JSONType
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
    id = Column(Integer, primary_key=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))

    @classmethod
    def authenticate(cls, app_id, password, request):
        app = request.db.query(cls).get(app_id)

        if app is not None and app.password == password:
            return (app_id, )

        return None

    @classmethod
    def get_authenticated_object(cls, request):
        try:
            [app_id] = request.authenticated_userid
        except TypeError:
            raise HTTPUnauthorized()

        return request.db.query(cls).get(app_id)
