import os
import base64
import unicodedata


def make_password(bit_length=15):
    """ Returns a random password string
    """
    return base64.b64encode(os.urandom(bit_length))


def username_preparer(value):
    return unicodedata.normalize('nfkc', value)
