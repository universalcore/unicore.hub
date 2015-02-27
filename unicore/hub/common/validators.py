import colander


email_validator = colander.Email()


def msisdn_validator(node, value):
    pass  # TODO - must raise colander.Invalid


def username_validator(node, value):
    pass  # TODO - must raise colander.Invalid


def app_data_validator(node, value):
    if not isinstance(value, dict):
        raise colander.Invalid(node,
                               '%(v)r is not a dictionary' % {'v': value})

    for key in value.keys():
        if not isinstance(key, int) or key < 0:
            raise colander.Invalid(node,
                                   '%(v)r is not a valid app ID' % {'v': key})

    for data in value.values():
        if not isinstance(data, dict):
            raise colander.Invalid(node,
                                   '%(v)r is not a dictionary' % {'v': data})
