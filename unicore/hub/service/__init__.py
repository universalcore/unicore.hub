import logging

from pyramid.authentication import (BasicAuthAuthenticationPolicy,
                                    SessionAuthenticationPolicy)
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import default_locale_negotiator
from pyramid_beaker import set_cache_regions_from_settings
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)


Base = declarative_base()
includes = [
    'cornice',
    'pyramid_jinja2',
    'pyramid_beaker',
    'pyramid_celery'
]


def db(request):
    maker = request.registry.dbmaker
    session = maker()

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()

    request.add_finished_callback(cleanup)

    return session


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    for include in includes:
        config.include(include)

    config.add_route('user-login', '/sso/login')
    config.add_route('user-logout', '/sso/logout')
    config.add_route('user-validate', '/sso/validate')
    config.add_route('user-join', '/sso/join')
    config.scan()

    # static resources setup
    config.add_static_view(
        name='static', path='unicore.hub:service/sso/static')

    # sqlalchemy setup
    engine = engine_from_config(settings)
    config.registry.dbmaker = sessionmaker(bind=engine)
    # NOTE: db session is tied to request lifespan
    config.add_request_method(db, reify=True)

    # beaker and cache setup
    set_cache_regions_from_settings(settings)

    # auth setup
    from unicore.hub.service.models import App, User
    from unicore.hub.service.authentication import PathAuthenticationPolicy
    basic_authn_policy = BasicAuthAuthenticationPolicy(
        check=App.authenticate,
        realm='apps')
    session_authn_policy = SessionAuthenticationPolicy(
        callback=User.verify_identifier)
    authn_policy = PathAuthenticationPolicy(
        path_map=[(r'/sso/(login|logout|join)', session_authn_policy)],
        default=basic_authn_policy)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    # translation setup
    config.add_translation_dirs('unicore.hub:service/locale/')
    config.set_locale_negotiator(default_locale_negotiator)

    return config.make_wsgi_app()
