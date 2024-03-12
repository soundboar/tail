from enum import StrEnum
from typing import Callable, TypeVar
from os import environ

from soundboar import __title__

Value = TypeVar('Value')
DefaultValue = TypeVar('DefaultValue')

PREFIX = __title__.upper() + "_"


class Var(StrEnum):
    DIRECTORY = "DIRECTORY"
    HOST = "HOST"
    PORT = "PORT"
    CORS_ORIGIN = "CORS_ORIGIN"


def get(
        name: str,
        default: DefaultValue = None,
        parser: Callable[[str], Value] = lambda x: x,
        prefix: str = PREFIX
) -> Value | DefaultValue:
    value = environ.get(prefix + name, default)
    if value is None:
        return default
    return parser(value)


def set(
        name: str,
        value: str,
        prefix: str = PREFIX
):
    environ[prefix + name] = value


def setdefault(
        name: str,
        value: str,
        prefix: str = PREFIX
):
    environ.setdefault(prefix + name, value)
