from pyramid.httpexceptions import HTTPUnauthorized
from sqlalchemy import Column, Integer, Unicode, event
from sqlalchemy.orm import Session
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import PasswordType, JSONType, ScalarListType

from unicore.hub.service import Base
from unicore.hub.service.utils import make_slugs


class ModelException(Exception):
    pass


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

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'app_data': self.app_data
        }


class App(Base):
    __tablename__ = 'apps'

    # TODO - extend to cover user api
    all_groups = (
        'group:apps_manager',  # Can create, view and edit apps
    )

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255), nullable=False)
    slug = Column(Unicode(255), unique=True, nullable=False)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']), nullable=False)
    groups = Column(ScalarListType())

    @classmethod
    def authenticate(cls, slug, password, request):
        app = request.db.query(cls) \
            .filter(cls.slug == slug) \
            .first()

        if app is not None and app.password == password:
            return [app.id, ] + (app.groups or [])

        return None

    @classmethod
    def get_authenticated_object(cls, request):
        [slug] = (request.authenticated_userid, )
        if slug is None:
            raise HTTPUnauthorized()

        return request.db.query(App) \
            .filter(App.slug == slug) \
            .one()

    def set_unique_slug(self, session, exclude=()):
        if self.title is None:
            raise ModelException(
                "%r 'title' field is required" % self.__class__)

        # NOTE: race condition, but I'm leaving it to the
        # database to raise an exception
        for slug in make_slugs(self.title):
            if slug in exclude:
                continue
            q = session.query(self.__class__) \
                .filter(self.__class__.slug == slug) \
                .exists()
            if session.query(q).scalar():
                continue
            self.slug = slug
            break

        return self.slug

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'groups': self.groups
        }


@event.listens_for(Session, 'before_flush')
def set_derived_fields(session, flush_context, instances):
    """ Sets derived, autogenerated fields like slug once-off
    """
    with session.no_autoflush:  # don't flush until slug is set
        new_slugs = set()

        for obj in session.new:
            if isinstance(obj, App):
                slug = obj.set_unique_slug(session, exclude=new_slugs)
                new_slugs.add(slug)
