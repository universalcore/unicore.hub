import colander

from unicore.hub.service.validators import (username_validator,
                                            app_data_validator,
                                            pin_validator)
from unicore.hub.service.utils import username_preparer
from unicore.hub.service.models import App as AppModel, User as UserModel


class User(colander.MappingSchema):
    username = colander.SchemaNode(
        colander.String(),
        preparer=username_preparer,
        validator=colander.All(
            colander.Length(UserModel.username_length),
            username_validator))
    password = colander.SchemaNode(
        colander.String(),
        validator=pin_validator(length=4))
    app_data = colander.SchemaNode(
        colander.Mapping(unknown='preserve'),
        validator=app_data_validator,
        missing=None)


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(AppModel.all_groups))


class App(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=AppModel.title_length))
    groups = Groups(missing=[])
