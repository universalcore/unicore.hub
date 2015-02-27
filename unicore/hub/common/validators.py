import colander


def username_validator(node, value):
    # http://stackoverflow.com/questions/1597743/what-restrictions-should-i-impose-on-usernames
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
