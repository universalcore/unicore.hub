import colander

from unicore.hub.common.validators import (msisdn_validator,
                                           username_validator,
                                           email_validator,
                                           app_data_validator)


# TODO - generate schemas from Postgres models?


class User(colander.MappingSchema):
    user_id = colander.SchemaNode(colander.Int())
    username = colander.SchemaNode(colander.String(),
                                   validator=username_validator)
    msisdn = colander.SchemaNode(colander.String(),
                                 validator=msisdn_validator,
                                 missing=None)
    email = colander.SchemaNode(colander.String(),
                                validator=email_validator,
                                missing=None)
    app_data = colander.SchemaNode(colander.Mapping(unknown='preserve'),
                                   validator=app_data_validator)
