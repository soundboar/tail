import os
import pathlib
import shutil
import zipfile
from io import BytesIO

import click


@click.group()
@click.option("--log-level",
              type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], case_sensitive=False),
              default="NOTSET")
@click.option("--dir", "directory", default=None, type=click.Path(file_okay=False), required=False,
              help="Root directory of soundboars data-files (which contains database and sound files)")
def cli(directory: str, log_level: str):
    from soundboar.logs import setup

    setup(log_level)

    from soundboar.logs import logger
    from soundboar import __title__, __version__
    logger.debug(f"Running {__title__} version {__version__}")

    from platformdirs import user_data_dir
    from soundboar.util import env
    if directory:
        env.set(env.Var.DIRECTORY, directory)
    else:
        env.setdefault(env.Var.DIRECTORY, user_data_dir(__title__, __title__))
    logger.info(f"Repo directory: {env.get(env.Var.DIRECTORY)}")


@click.command()
@click.option("--mkdir", is_flag=True, default=True, help="Create the directory if it doesn't exist")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing dirs")
@click.option("--exist-ok", is_flag=True, default=False,
              help="Do not throw an error if the data directory already exists")
@click.option("--skip-head", is_flag=True, default=False, help="Do not download and install the frontend")
@click.option("--overwrite-head", is_flag=True, default=False, help="Overwrite existing frontend files")
@click.option("--head-version", default=None, help="Frontend version to install, defaults to corresponding tail version")
def install(
        mkdir: bool = True,
        force: bool = False,
        exist_ok: bool = True,
        skip_head: bool = False,
        overwrite_head: bool = False,
        head_version: str = None
):
    """Install soundboar by creating its data directory"""
    from soundboar import __default_data_dir__, __version__
    from soundboar.util import env
    from soundboar.logs import logger
    path = env.get(env.Var.DIRECTORY, parser=pathlib.Path).resolve()
    if path.exists():
        if len(os.listdir(path)) != 0 and not force:
            logger.info(f"Not installing, already exists")
            if exist_ok:
                return
            else:
                raise click.ClickException(f"Data directory {path} already exists")
    elif mkdir:
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        raise click.ClickException("Data directory does not exist")
    shutil.copytree(__default_data_dir__, path, dirs_exist_ok=force)
    if not skip_head:
        import requests
        from http import HTTPStatus
        head_version = head_version or __version__
        if head_version[0] == "v":
            head_version = head_version[1:]
        default_line_identifier = "soundboar-default-static"
        url = f"https://github.com/soundboar/head/releases/download/v{head_version}/dist.zip"
        subdir = "dist/"
        dest_dir = str(env.get(env.Var.DIRECTORY, parser=pathlib.Path) / "static") + "/"
        response = requests.get(url)
        if response.status_code != HTTPStatus.OK.value:
            logger.error(f"Could not install frontend as the matching/requested version was not found. Expected: {url}")
        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            logger.info(f"Downloading files from {url} (subdir={subdir}) to {dest_dir}")
            for member in zip_file.infolist():
                if not member.filename.startswith(subdir) or member.is_dir():
                    continue
                new_path = pathlib.Path(member.filename.replace(subdir, dest_dir))
                if new_path.exists() and not overwrite_head:
                    try:
                        with open(new_path, 'r') as file:
                            if default_line_identifier not in file.readline():
                                logger.warn(f"Not overwriting {new_path} as it is not a default file")
                                continue
                    except UnicodeDecodeError:
                        logger.warn(f"Not overwriting {new_path} as it is not a text file")
                        continue
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                with zip_file.open(member, "r") as source, open(new_path, "wb") as destination:
                    shutil.copyfileobj(source, destination)

    logger.info(f"Installed soundboar to {path}")


@click.command()
def uninstall():
    """Delete soundboars data directory. Does not check if it is a soundboar data directory, simply just removes it
    recursively"""
    from soundboar.util import env
    shutil.rmtree(env.get(env.Var.DIRECTORY, parser=pathlib.Path).resolve())


@click.command()
@click.option("--no-install", is_flag=True, default=False,
              help="Do not install but abort if the data directory does not exist or is empty")
@click.option('--development', is_flag=True, help="Run in development mode with hot-reload")
@click.option('--cors-origin', default=None, help="Allow a specific cors origin")
@click.pass_context
def run(
        ctx: click.Context,
        no_install: bool,
        development: bool,
        cors_origin: str | None
):
    """Run soundboar"""
    if not no_install:
        ctx.invoke(install, exist_ok=True)

    log_level = ctx.parent.params["log_level"].lower()
    if log_level != "notset":
        kwargs = {
            "log_level": ctx.parent.params["log_level"].lower()
        }
    else:
        kwargs = {}

    from soundboar.logs import setup
    from soundboar.util import env
    log_config = setup()
    if development:
        kwargs |= {"reload": True}
        if not cors_origin and not env.get(env.Var.CORS_ORIGIN):
            cors_origin = "http://localhost:5173"
    if cors_origin:
        env.set(env.Var.CORS_ORIGIN, cors_origin)

    import uvicorn
    from soundboar.util import env
    uvicorn.run("soundboar.app.app:app",
                log_config=log_config,
                host=env.get(env.Var.HOST, "127.0.0.1"),
                port=env.get(env.Var.PORT, 8000, int),
                **kwargs)


cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(run)
