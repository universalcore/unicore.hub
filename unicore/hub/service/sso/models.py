import re
from datetime import datetime, timedelta
import time
import random

from sqlalchemy import Column, Unicode, ForeignKey, DateTime, Boolean
from sqlalchemy_utils import UUIDType

from unicore.hub.service import Base
from unicore.hub.service.sso.utils import same_origin, clean_url


TICKET_EXPIRE = 90
TICKET_RAND_LEN = 32
TICKET_RE = re.compile(
    '^[A-Z]{2,3}-[0-9]{10,}-[a-zA-Z0-9]{%d}$' % TICKET_RAND_LEN)
TICKET_PREFIX = 'ST'
TICKET_ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyz' \
                       'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


class TicketValidationError(Exception):
    pass


class InvalidTicket(TicketValidationError):
    pass


class InvalidRequest(TicketValidationError):
    pass


class InvalidService(TicketValidationError):
    pass


def calculate_expiration():
    return datetime.utcnow() + timedelta(seconds=TICKET_EXPIRE)


def make_ticket_string():
    rand_str = ''.join(
        random.choice(TICKET_ALLOWED_CHARS) for i in range(TICKET_RAND_LEN))
    return '%s-%d-%s' % (TICKET_PREFIX, int(time.time()), rand_str)


class Ticket(Base):
    __tablename__ = 'tickets'

    ticket = Column(
        Unicode(255), default=make_ticket_string, primary_key=True)
    user_id = Column(
        UUIDType(binary=False), ForeignKey('users.uuid'), nullable=False)
    expires = Column(DateTime, default=calculate_expiration, nullable=False)
    consumed = Column(DateTime)
    service = Column(Unicode(255), nullable=False)
    primary = Column(Boolean, nullable=False, default=False)

    @classmethod
    def create_ticket_from_request(cls, request, **attrs):
        ticket = Ticket()

        try:
            [ticket.user_id] = request.authenticated_userid
        except (TypeError, AttributeError):
            if 'user_id' not in attrs:
                raise InvalidRequest('No authenticated user id provided')

        ticket.service = clean_url(request.GET['service'])
        for attr, value in attrs.iteritems():
            setattr(ticket, attr, value)

        request.db.add(ticket)
        request.db.flush()
        return ticket

    def consume(self, request):
        self.consumed = datetime.utcnow()
        request.db.flush()

    @classmethod
    def consume_all(cls, user_id, request):
        now = datetime.utcnow()
        request.db.query(cls) \
            .filter(cls.user_id == user_id) \
            .filter(cls.expires > now) \
            .update({'consumed': now})
        request.db.flush()

    @property
    def is_consumed(self):
        return self.consumed is not None

    @property
    def is_expired(self):
        return self.expires <= datetime.utcnow()

    @property
    def is_primary(self):
        return self.primary

    @classmethod
    def validate(cls, request):
        service = request.GET.get('service', None)
        ticket_str = request.GET.get('ticket', None)
        renew = bool(request.GET.get('renew', False))

        if not ticket_str:
            raise InvalidTicket('No ticket string provided')

        if not TICKET_RE.match(ticket_str):
            raise InvalidTicket('Ticket string %s is invalid' % ticket_str)

        ticket = request.db.query(cls) \
            .filter(cls.ticket == ticket_str) \
            .first()

        if ticket is None:
            raise InvalidTicket('Ticket %s does not exist' % ticket_str)

        if ticket.is_consumed:
            raise InvalidTicket('Ticket %s has already been used' % ticket_str)

        ticket.consume()

        if ticket.is_expired:
            raise InvalidTicket('Ticket %s has expired' % ticket_str)

        if not service:
            raise InvalidRequest('No service identifier provided')

        # TODO: restrict service
        # if not is_valid_service_url(service):
        #     raise InvalidService('Service %s is not a valid %s URL' %
        #                          (service, t.name))

        if not same_origin(ticket.service, service):
            raise InvalidService(
                'Ticket %s for service %s is invalid for service %s' %
                (ticket, ticket.service, service))

        if renew and not ticket.is_primary:
            raise InvalidTicket(
                'Ticket %s was not issued via primary credentials' % ticket)

        return ticket
