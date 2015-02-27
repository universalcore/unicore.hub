import colander

from unicore.hub.common.validators import (username_validator,
                                           app_data_validator)


# TODO - generate schemas from Postgres models?


class User(colander.MappingSchema):
    user_id = colander.SchemaNode(colander.Int())
    username = colander.SchemaNode(colander.String(),
                                   validator=username_validator)
    app_data = colander.SchemaNode(colander.Mapping(unknown='preserve'),
                                   validator=app_data_validator)
