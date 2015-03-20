from uuid import uuid4, UUID

from pyramid.httpexceptions import HTTPUnauthorized
from sqlalchemy import Column, Unicode, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import (PasswordType, JSONType, ScalarListType, UUIDType,
                              URLType)

from unicore.hub.service import Base
from unicore.hub.service import utils


class UUIDMixin(object):
    _uuid = Column(
        UUIDType(binary=False), name='uuid', default=uuid4,
        primary_key=True)

    @property
    def uuid(self):
        return self._uuid.hex

    @uuid.setter
    def uuid(self, value):
        if isinstance(value, UUID):
            self._uuid = value
        else:
            self._uuid = UUID(hex=value)

    @classmethod
    def get_authenticated_object(cls, request):
        [uuid] = (request.authenticated_userid, )
        if uuid is None:
            raise HTTPUnauthorized()

        return request.db.query(cls).get(uuid)


class User(Base, UUIDMixin):
    __tablename__ = 'users'

    username_length = 255

    username = Column(Unicode(username_length), unique=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))
    app_data = Column(MutableDict.as_mutable(JSONType))
    created = Column(DateTime(), default=func.now(), nullable=False)

    tickets = relationship('Ticket', backref='user', lazy='dynamic')

    @classmethod
    def authenticate(cls, username, password, request):
        user = request.db.query(cls) \
            .filter(cls.username == username) \
            .first()

        if user is not None and user.password == password:
            return (user.uuid, )

        return None

    @classmethod
    def verify_identifier(cls, uuid, request):
        user = request.db.query(cls).get(uuid)

        if user is not None:
            return (user.uuid, )

        return None

    def to_dict(self):
        return {
            'uuid': self.uuid,
            'username': self.username,
            'app_data': self.app_data
        }


class App(Base, UUIDMixin):
    __tablename__ = 'apps'

    # TODO - extend to cover user api
    all_groups = (
        'group:apps_manager',  # Can create, view and edit apps
    )

    title_length = 255

    title = Column(Unicode(title_length), nullable=False)
    key = Column(Unicode(128), default=utils.make_key, nullable=False)
    url = Column(URLType())
    groups = Column(ScalarListType())
    created = Column(DateTime(), default=func.now(), nullable=False)

    @classmethod
    def authenticate(cls, uuid, key, request):
        app = request.db.query(cls).get(uuid)

        if app is not None and app.key == key:
            return [app.uuid, ] + (app.groups or [])

        return None

    def to_dict(self):
        return {
            'uuid': self.uuid,
            'key': self.key,
            'url': self.url,
            'title': self.title,
            'groups': self.groups
        }
