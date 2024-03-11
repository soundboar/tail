import enum
from datetime import datetime
from os import PathLike
from typing import Optional, AsyncIterator, Tuple, Iterator


class Player:
    """
    Player interface for the soundboards internal player.
    All players implementing this interface will be compatible with the player.
    """

    _last_error = None

    class State(enum.StrEnum):
        """
        States the player can be in.
        """

        INITIATED = "initiated"
        """Player was initiated but never had anything to play"""

        OPENING = "opening"
        """Player currently opens a file"""

        BUFFERING = "buffering"
        """Player buffers current file"""

        PLAYING = "playing"
        """Player plays current file"""

        PAUSED = "paused"
        """Player is currently paused in a file"""

        STOPPED = "stopped"
        """Player is currently stopped"""

        ENDED = "ended"
        """Player has ended playback"""

        ERROR = "error"
        """An error occurred"""

    class Event(enum.StrEnum):
        """
        Events the player emits when an event occurs.
        """
        STATE_CHANGE = "statechange"
        FILE_CHANGE = "filechange"
        # POSITION_CHANGE = "positionchange"
        VOLUME_CHANGE = "volumechange"
        ERROR = "error"

    def play(self, file: PathLike | str) -> str:
        """
        Play this file right now. Afterward, continue with the playlist
        :param file: File to play right now
        :return internal identifier which will be returned by identifier(),
            next_identifier(), or previous_identifier(). This value can (and
            should) be used to associate meta-data to the currently playing
            file if necessary.
        """
        raise NotImplementedError()

    def pause(self, state: bool | None = None) -> bool | None:
        """
        Play/pause the player
        :param state: True to play, False to pause, None to toggle
        :return: the new state
        """
        raise NotImplementedError()

    def stop(self):
        """
        Stop the playback and clear the playlist
        """
        raise NotImplementedError()

    def add(self, file: PathLike | str, index: Optional[int]) -> str:
        """
        Add a file to the end of the playlist or at the given index
        :param file: File to add to the playlist
        :param index: Index at which to insert the file
        :return internal identifier which will be returned by identifier(),
            next_identifier(), or previous_identifier(). This value can (and
            should) be used to associate meta-data to the currently playing
            file if necessary.
        """
        raise NotImplementedError()

    def remove(self, file_or_index: PathLike | str | int):
        """
        Remove a file from the playlist, if file: only removes first match
        :param file_or_index: File or index of the file to remove
        """
        raise NotImplementedError()

    def clear(self):
        """
        Clear the playlist (does not interrupt the current file)
        """
        raise NotImplementedError()

    def next(self):
        """
        Jump to the next file
        """
        raise NotImplementedError()

    def identifier(self, *, index: int | None = None, relative: int | None = None) -> str | None:
        """
        Identifier of the file at the given index or the current file if not given
        :param index: Index of the file to get the identifier, current file if none
        :param relative: Get the identifier relative to the current one +1 for next, -1 for previous (+2/-2/..)
        :return: Identifier of the current file
        """
        if index is not None and relative is not None:
            raise ValueError("Cannot specify both index and relative")
        if index is None:
            index = self.index()
        if index is None:
            return None
        if relative:
            index = index + relative
        identifier = list(self.identifiers_from_to(index, index))
        if len(identifier) > 0:
            return identifier[0]
        return None

    def duration(self, *, index: int | None = None, relative: int | None = None) -> int | None:
        """
        Duration of the file at the given index or the current file if not given
        :param index: Index of the file to get the identifier, current file if none
        :param relative: Get the duration relative to the current one +1 for next, -1 for previous (+2/-2/..)
        :return: Duration in ms
        """
        if index is not None and relative is not None:
            raise ValueError("Cannot specify both index and relative")
        if index is None:
            index = self.index()
        if index is None:
            return None
        if relative:
            index = index + relative
        duration = list(self.durations_from_to(index, index))
        if len(duration) > 0:
            return duration[0]
        return None

    def identifiers_from_to(self, start: int, end: int) -> Iterator[str]:
        """
        Get all identifiers of the files in the playlist from `start` to `end`
        :param start start of the file span to get the identifiers from
        :param end end of the file span to get the identifiers from
        :return: identifiers
        """
        raise NotImplementedError()

    def durations_from_to(self, start: int, end: int) -> Iterator[int]:
        """
        Get all durations of the files in the playlist from `start` to `end`
        :param start start of the file span to get the durations from
        :param end end of the file span to get the durations from
        :return: durations in ms
        """
        raise NotImplementedError()

    def all_identifiers(self) -> Iterator[str]:
        """
        Identifiers of all files in the playlist
        :return: Identifiers of all files in the playlist
        """
        return self.identifiers_from_to(0, self.size()-1)

    def all_durations(self) -> Iterator[int]:
        """
        Durations of all files in the playlist
        :return: Duration of all files in the playlist
        """
        return self.durations_from_to(0, self.size()-1)

    def previous_identifier(self) -> str | None:
        """
        Identifier of the previous playing file
        :return: Identifier of the previous playing file
        """
        return self.identifier(relative=-1)

    def previous_duration(self) -> int | None:
        """
        Duration of the previous playing file
        :return: Duration of the previous playing file
        """
        return self.duration(relative=-1)

    def next_identifier(self) -> str | None:
        """
        Identifier of the next playing file
        :return: Identifier of the next playing file
        """
        return self.identifier(relative=1)

    def next_duration(self) -> int | None:
        """
        Duration of the next playing file
        :return: Duration of the next playing file
        """
        return self.duration(relative=1)

    def restart(self):
        """
        Restart this file
        """
        raise NotImplementedError()

    def previous(self):
        """
        Jump to the previous file
        """
        raise NotImplementedError()

    def volume(self, volume: int | None = None) -> int:
        """
        Set/get the current volume
        :param volume: If not None: set the volume level (0-100)
        :return: get the current volume
        """
        raise NotImplementedError()

    def state(self) -> State:
        """
        Get the current state of the player
        :return: current state of the player
        """
        raise NotImplementedError()

    def index(self) -> int | None:
        """
        Position of the current file in the playlist
        :return: Position of the current file in the playlist
        """
        raise NotImplementedError()

    def size(self) -> int:
        """
        Number of items in the current playlist
        :return: Number of items in the current playlist
        """
        raise NotImplementedError()

    def position(self, position: float | None = None) -> float:
        """
        Set/Get the current position at the current track in percent
        :return:
        """
        raise NotImplementedError()

    def last_error(self) -> Tuple[datetime, str] | None:
        """
        Get the last error of the player and when it occurred
        :return: Error and when it occurred
        """
        return self._last_error

    def _add_error(self, msg: str):
        self._last_error = (datetime.now(), msg)

    async def on_event(self) -> AsyncIterator[Event]:
        """
        Get an infinite iterator which yields events without any further information
        Get further information yourself
        """
        raise NotImplementedError()
