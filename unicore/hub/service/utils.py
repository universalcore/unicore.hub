import os
import base64
import unicodedata

from pyramid.i18n import TranslationStringFactory


def make_password(bit_length=15):
    """ Returns a random password string
    """
    return base64.b64encode(os.urandom(bit_length))


def normalize_unicode(value):
    if isinstance(value, basestring):
        return unicodedata.normalize('NFKC', unicode(value))
    return value


translation_string_factory = TranslationStringFactory(None)
