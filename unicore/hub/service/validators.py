import re

import colander


# exclude control characters
USERNAME_DISALLOWED_CHARS = u'\u0000-\u001f\u007f-\u009f'
# have a look at http://unicode.org/reports/tr20/#Suitable
# only excluding bidi controls
USERNAME_DISALLOWED_CHARS += u'\u202a-\u202e'
USERNAME_DISALLOWED_CHARS = re.compile(u'[%s]' % USERNAME_DISALLOWED_CHARS)


def username_validator(node, value):
    # http://stackoverflow.com/questions/1597743/what-restrictions-should-i-impose-on-usernames
    # must be longer than 1 character
    if len(value) == 0:
        raise colander.Invalid('Username must be at least 1 character long')

    # disallow leading and trailing space
    if value[0] == ' ':
        raise colander.Invalid('%r has leading space' % (value, ))
    if value[-1] == ' ':
        raise colander.Invalid('%r has trailing space' % (value, ))

    # disallow more than one space in a row
    if '  ' in value:
        raise colander.Invalid('%r has more than 1 space in a row' % (value, ))

    if USERNAME_DISALLOWED_CHARS.search(value):
        raise colander.Invalid(
            '%r may not contain control characters' % (value, ))


def app_data_validator(node, value):
    if not isinstance(value, dict):
        raise colander.Invalid(
            node, '%r is not a dictionary' % (value, ))

    for key in value.keys():
        if not isinstance(key, basestring) or len(key) != 32:
            raise colander.Invalid(
                node, '%r is not a valid app UUID' % (key, ))

    for data in value.values():
        if not isinstance(data, dict):
            raise colander.Invalid(
                node, '%r is not a dictionary' % (data, ))


def pin_validator(length):

    def validator(node, value):
        if len(value) != length:
            raise colander.Invalid(
                node, '%r is not %d digits long' % (value, length))

        non_numeric = filter(lambda ch: not ch.isdigit(), value)
        if non_numeric:
            raise colander.Invalid(
                node, '%r is not a numeric string' % (value, ))

    return validator
