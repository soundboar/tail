from pathlib import Path

from pydantic import BaseModel


class File(BaseModel):
    id: str
    name: str
    location: Path

    @classmethod
    def from_tuple(cls, tpl):
        return File(id=tpl[0], name=tpl[1], location=tpl[2])


class Test(BaseModel):
    wat: str
