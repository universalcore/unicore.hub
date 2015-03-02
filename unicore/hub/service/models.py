from sqlalchemy import Column, Integer, Unicode
from sqlalchemy_utils import PasswordType, JSONType

from unicore.hub.service import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255), unique=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))
    app_data = Column(JSONType)


class App(Base):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    password = Column(PasswordType(schemes=['pbkdf2_sha256']))
