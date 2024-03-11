import asyncio
import pathlib
from enum import Enum
from http import HTTPStatus
from io import BytesIO
from pathlib import Path

import requests
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.websockets import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import FileResponse

from soundboar import __title__, __version__, __source_root_dir__
from soundboar.repository.Repository import Repository
from soundboar.player import VLCPlayer
from soundboar.app.api_types import File, Test
from soundboar.player.Player import Player
from soundboar.util import extract_meta, check_valid_audio_url, to_file_id, env
from soundboar.util.openapi import custom_openapi

api = FastAPI()

if env.get(env.Var.CORS_ORIGIN) is not None:
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[env.get(env.Var.CORS_ORIGIN)],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

supported_files = {".mp3", ".ogg", ".wav", ".flac"}
repo = Repository(env.get(env.Var.DIRECTORY, parser=pathlib.Path) / "sounds", supported_files)
player = VLCPlayer()


@api.get("/websocket_debug")
def websocket_debug():
    return HTMLResponse(content=(__source_root_dir__ / "api" / "websocket.html").read_text())


@api.get("/files")
def files() -> dict[str, File]:
    return dict(map(lambda x: (x[0], File.from_tuple(x)), repo.all()))


@api.post("/play/{file_id}")
def play(file_id: str):
    player.play(repo.file(file_id))


@api.get("/download/{file_id}")
def download(file_id: str):
    file = repo.file(file_id)
    if not file.exists():
        raise HTTPException(404, detail=f"File with ID {file_id} does not exist")
    filename = file_id
    if not filename.endswith(file.suffix):
        filename += file.suffix
    return FileResponse(file, media_type='application/octet-stream', filename=filename)


@api.post("/pause")
def pause(do_pause: bool | None = None) -> bool | None:
    return player.pause(do_pause)


@api.post("/next")
def next_():
    return player.next()


@api.post("/previous")
def previous():
    return player.previous()


@api.post("/add/{file_id}")
def add(file_id: str):
    player.add(repo.file(file_id))


@api.post("/stop")
def stop():
    player.stop()


@api.post("/clear")
def clear():
    player.clear()


@api.get("/duration")
def duration() -> int:
    return player.duration()


@api.get("/state")
def state() -> Player.State:
    return player.state()


@api.post("/file/{request_file_id}")
async def upload_file(request_file_id: str, file: UploadFile) -> tuple[File, int]:
    file_id = to_file_id(request_file_id, file.filename, supported_files)
    return File.from_tuple(await repo.write(file.file, file_id)), repo.file_position(file_id)


@api.get("/meta/og-title/{website:path}")
async def get_og_title(website: str) -> str | None:
    data = await extract_meta(website, "og:title", "og:audio")
    check_valid_audio_url(data["og:audio"], supported_files)
    return data["og:title"]


@api.post("/upload_from_url/{request_file_id}/{website:path}")
async def upload_from_url(request_file_id: str, website: str) -> tuple[File, int]:
    data = await extract_meta(website, "og:audio")
    check_valid_audio_url(data["og:audio"], supported_files)
    file_id = to_file_id(request_file_id, data["og:audio"], supported_files)
    response = await asyncio.to_thread(requests.get, data["og:audio"], headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    return File.from_tuple(await repo.write(BytesIO(response.content), file_id)), repo.file_position(file_id)


@api.delete("/file/{file_id}")
def delete_file(file_id: str):
    repo.delete(file_id)


@api.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async for event in player.on_event():
        await websocket.send_text(str(event))


custom_openapi(api, Player.Event)
