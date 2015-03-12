from unicore.hub.service.tests import DBTestCase
from unicore.hub.service.sso.models import Ticket


class SSOTestCase(DBTestCase):

    def create_ticket(self, session=None, **attrs):
        return self.create_model_object(Ticket, session, **attrs)
