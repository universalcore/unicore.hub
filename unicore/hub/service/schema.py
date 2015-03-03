import colander

from unicore.hub.service.validators import (username_validator,
                                            app_data_validator,
                                            pin_validator)
from unicore.hub.service.models import App


class User(colander.MappingSchema):
    username = colander.SchemaNode(colander.String(),
                                   validator=username_validator)
    password = colander.SchemaNode(colander.String(),
                                   validator=pin_validator(length=4))
    app_data = colander.SchemaNode(colander.Mapping(unknown='preserve'),
                                   validator=app_data_validator,
                                   missing=None)


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(colander.String(),
                                validator=colander.OneOf(App.all_groups))


class App(colander.MappingSchema):
    groups = Groups(missing=[])
