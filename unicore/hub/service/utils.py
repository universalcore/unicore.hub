import os
import base64
from itertools import count

from slugify import slugify


def make_password(bit_length=15):
    """ Returns a random password string
    """
    return base64.b64encode(os.urandom(bit_length))


def make_slugs(s):
    """ Generates slugs for the given string in ascending order
    """
    slug = slugify(s)
    yield unicode(slug)
    for i in count(2):
        yield u'%s-%s' % (slug, i)
