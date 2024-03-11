from os import PathLike
from pathlib import Path

from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles

from soundboar.app.api import api
from soundboar.util import env

STATIC_FILES = env.Var.DIRECTORY
app = FastAPI()


class FallbackStaticFiles(StaticFiles):
    def __init__(self, fallback: PathLike | str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__fallback = fallback

    async def get_response(self, path: str, *args, **kwargs) -> Response:
        try:
            return await super().get_response(path, *args, **kwargs)
        except HTTPException as e:
            if e.status_code != 404:
                raise e
            try:
                return await super().get_response(str(self.__fallback), *args, **kwargs)
            except Exception as ee:
                raise ee from e


app.mount("/api", api, name="api")
static_files = FallbackStaticFiles(
    fallback="index.html",
    directory=env.get(env.Var.DIRECTORY, parser=Path) / "static",
    html=True
)
app.mount("/", static_files, name="app")
