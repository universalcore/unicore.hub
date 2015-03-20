import colander

from unicore.hub.service import validators as vld
from unicore.hub.service.utils import normalize_unicode


class User(colander.MappingSchema):
    username = colander.SchemaNode(
        colander.String(),
        preparer=normalize_unicode,
        validator=vld.username_validator)
    password = colander.SchemaNode(
        colander.String(),
        validator=vld.pin_validator(length=4))
    app_data = colander.SchemaNode(
        colander.Mapping(unknown='preserve'),
        validator=vld.app_data_validator,
        missing=None)


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(
        colander.String(),
        validator=vld.app_groups_validator)


class App(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        validator=vld.app_title_validator)
    url = colander.SchemaNode(
        colander.String(),
        validator=vld.app_url_validator,
        missing=None)
    groups = Groups(missing=[])
