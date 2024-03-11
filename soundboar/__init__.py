import pathlib
from importlib import metadata

__title__ = __package__
__version__ = metadata.version(__package__)
__source_root_dir__ = pathlib.Path(__file__).parent.resolve()
__root_dir__ = __source_root_dir__.parent.resolve()
__default_data_dir__ = (__source_root_dir__ / 'default_data').resolve()
