from itertools import count

from slugify import slugify


def make_slugs(s):
    """ Generates slugs for the given string in ascending order
    """
    slug = slugify(s)
    yield unicode(slug)
    for i in count(2):
        yield u'%s-%s' % (slug, i)
