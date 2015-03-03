import os
import base64


def make_password(bit_length=15):
    return base64.b64encode(os.urandom(bit_length))
