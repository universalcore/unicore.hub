import os
import hmac
import uuid
import base64
import unicodedata
from hashlib import sha1

from pyramid.i18n import TranslationStringFactory


def make_password(bit_length=15):
    """ Returns a random password string
    """
    return base64.b64encode(os.urandom(bit_length))


def make_key():
    return hmac.new(uuid.uuid4().bytes, digestmod=sha1).hexdigest()


def normalize_unicode(value):
    if isinstance(value, basestring):
        return unicodedata.normalize('NFKC', unicode(value))
    return value


translation_string_factory = TranslationStringFactory(None)
