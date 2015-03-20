import re

import colander

from unicore.hub.service.models import App as AppModel, User as UserModel
from unicore.hub.service.utils import translation_string_factory as _


""" User schema validators
"""


# exclude control characters
USERNAME_DISALLOWED_CHARS = u'\u0000-\u001f\u007f-\u009f'
# have a look at http://unicode.org/reports/tr20/#Suitable
# only excluding bidi controls
USERNAME_DISALLOWED_CHARS += u'\u202a-\u202e'
USERNAME_DISALLOWED_CHARS = re.compile(u'[%s]' % USERNAME_DISALLOWED_CHARS)


def username_char_validator(node, value):
    # http://stackoverflow.com/questions/1597743/what-restrictions-should-i-impose-on-usernames
    mapping = {'username': value}

    # disallow leading and trailing space
    if value[0] == ' ':
        raise colander.Invalid(
            node, _('${username} has leading space', mapping=mapping))
    if value[-1] == ' ':
        raise colander.Invalid(
            node, _('${username} has trailing space', mapping=mapping))

    # disallow more than one space in a row
    if '  ' in value:
        raise colander.Invalid(
            node,
            _('${username} has more than 1 space in a row', mapping=mapping))

    if USERNAME_DISALLOWED_CHARS.search(value):
        raise colander.Invalid(
            node,
            _('${username} contains control characters', mapping=mapping))


username_length_validator = colander.Length(
    min=1, max=UserModel.username_length)


@colander.deferred
def username_validator(node, kw):
    request = kw.get('request')

    def username_unique_validator(node, value):
        user = request.db.query(UserModel) \
            .filter(UserModel.username == value) \
            .first()
        if user:
            raise colander.Invalid(
                node,
                _('${username} is not unique', mapping={'username': value}))

    return colander.All(
        username_length_validator,
        username_char_validator,
        username_unique_validator)


def app_data_validator(node, value):

    if not isinstance(value, dict):
        raise colander.Invalid(
            node, _('${data} is not a dictionary', mapping={'data': value}))

    for key in value.keys():
        if not isinstance(key, basestring) or len(key) != 32:
            raise colander.Invalid(
                node,
                _('${key} is not a valid app UUID', mapping={'key': key}))

    for data in value.values():
        if not isinstance(data, dict):
            raise colander.Invalid(
                node,
                _('${data} is not a dictionary', mapping={'data': data}))


def pin_validator(length):

    def validator(node, value):
        if len(value) != length:
            raise colander.Invalid(
                node,
                _('${pin} is not ${length} digits long',
                  mapping={'pin': value, 'length': length}))

        non_numeric = filter(lambda ch: not ch.isdigit(), value)
        if non_numeric:
            raise colander.Invalid(
                node,
                _('${pin} contains non-digit characters',
                  mapping={'pin': value}))

    return validator


""" App schema validators
"""


app_title_validator = colander.All(
    colander.Length(max=AppModel.title_length))
app_groups_validator = colander.OneOf(AppModel.all_groups)
app_url_validator = colander.url
