from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


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

    # sqlalchemy setup
    config.scan('%s.models' % __name__)
    config.scan('%s.user_api' % __name__)
    config.scan('%s.app_api' % __name__)
    engine = engine_from_config(settings)
    config.registry.dbmaker = sessionmaker(bind=engine)
    # NOTE: db session is tied to request lifespan
    config.add_request_method(db, reify=True)

    # auth setup
    from unicore.hub.service.models import App
    authn_policy = BasicAuthAuthenticationPolicy(
        check=App.authenticate,
        realm='apps')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    return config.make_wsgi_app()
