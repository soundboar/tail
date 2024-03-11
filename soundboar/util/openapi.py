from enum import Enum, IntEnum

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from soundboar import __title__, __version__


def enum_to_schema(enum: Enum, name: str | None = None) -> dict[str, any]:
    """Generate a JSON Schema definition for an enum."""
    name = name or enum.__name__
    return {
        "type": "integer" if isinstance(enum, IntEnum) else "string",
        "title": name,
        "description": (enum.__doc__ or f"An enumeration of {name}").strip(),
        "enum": [item.value for item in enum],
    }


def custom_openapi(app_: FastAPI, *include_models: type[BaseModel | Enum]):
    if app_.openapi_schema:
        return app_.openapi_schema
    openapi_schema = get_openapi(
        title=f"{__title__} API",
        version=__version__,
        routes=app_.routes
    )
    schemas = openapi_schema["components"]["schemas"]
    for model in include_models:
        if model.__name__ in schemas:
            raise ValueError(f"Model {model.__name__} already registered")
        if issubclass(model, Enum):
            schemas[model.__name__] = enum_to_schema(model)
        else:
            schemas[model.__name__] = model.schema()

    app_.openapi_schema = openapi_schema
    return app_.openapi_schema
