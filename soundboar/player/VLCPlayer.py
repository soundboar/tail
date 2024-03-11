from os import PathLike
from typing import Iterator, AsyncIterator

from vlc import MediaListPlayer, EventType, Media, MediaList, Instance, MediaPlayer, MediaParsedStatus

from soundboar.util.CallbackToAsync import MakeAsync
from soundboar.player import Player


class VLCPlayer(Player):
    media_list_player: MediaListPlayer = None
    media_list: MediaList = None
    async_events: MakeAsync = None

    EVENT_MAPPING = {
        EventType.MediaPlayerMediaChanged: Player.Event.FILE_CHANGE,
        EventType.MediaPlayerEncounteredError: Player.Event.ERROR,
        EventType.MediaPlayerPaused: Player.Event.STATE_CHANGE,
        EventType.MediaPlayerPlaying: Player.Event.STATE_CHANGE,
        EventType.MediaPlayerStopped: Player.Event.STATE_CHANGE,
        EventType.MediaPlayerEndReached: Player.Event.STATE_CHANGE,
        EventType.MediaPlayerOpening: Player.Event.STATE_CHANGE,
        EventType.MediaPlayerAudioVolume: Player.Event.VOLUME_CHANGE,
    }

    STATE_MAPPING = {
        0: Player.State.INITIATED,
        1: Player.State.OPENING,
        2: Player.State.BUFFERING,
        3: Player.State.PLAYING,
        4: Player.State.PAUSED,
        5: Player.State.STOPPED,
        6: Player.State.ENDED,
        7: Player.State.ERROR
    }

    @property
    def media_player(self) -> MediaPlayer:
        return self.media_list_player.get_media_player()

    @property
    def instance(self) -> Instance:
        return self.media_player.get_instance()

    @property
    def media(self) -> Media | None:
        return self.media_player.get_media()

    def __init__(self):
        self.media_list = MediaList()
        self.media_list_player = MediaListPlayer()
        self.media_list_player.set_media_list(self.media_list)
        self.async_events = MakeAsync()
        event_manager = self.media_player.event_manager()
        for event in self.EVENT_MAPPING:
            event_manager.event_attach(event, self.handle_event)

    def handle_event(self, event):
        self.async_events.event(self.EVENT_MAPPING[event.type])

    def play(self, file: PathLike | str):
        current_media = self.media_player.get_media()
        if current_media:
            current_index = self.media_list.index_of_item(current_media)
        else:
            current_index = self.media_list.count() - 1
        self.add(file, current_index + 1)
        self.media_list_player.play_item_at_index(current_index + 1)
        return self.media_player.get_media().get_mrl()

    def pause(self, state: bool | None = None) -> bool:
        if state is None:
            state = self.media_list_player.is_playing()
        self.media_list_player.set_pause(state)
        return state

    def stop(self):
        self.media_list_player.stop()
        self.clear()

    def add(self, file: PathLike | str, index: int | None = None) -> str:
        media = Media(file)
        if index:
            self.media_list.insert_media(media, index)
        else:
            self.media_list.add_media(media)
        return media.get_mrl()

    def remove(self, file_or_index: PathLike | str | int):
        if not isinstance(file_or_index, int):
            # TODO: check if the following line really works.
            file_or_index = self.media_list.index_of_item(Media(file_or_index))
            if file_or_index == -1:
                self._add_error(f"remove: File {file_or_index} not found")
                return
        if file_or_index < 0:
            file_or_index = self.media_list.count() - file_or_index
        self.media_list.remove_index(file_or_index)

    def clear(self):
        while self.media_list.remove_index(0) == 0:
            pass

    def next(self):
        self.media_list_player.next()

    def restart(self):
        self.position(0)

    def previous(self):
        self.media_list_player.previous()

    def volume(self, volume: int | None = None) -> int:
        if volume is not None:
            self.media_player.audio_set_volume(volume)
        return self.media_player.audio_get_volume()

    def state(self):
        return self.STATE_MAPPING[self.media_player.get_state().value]

    def position(self, position: float | None = None) -> float:
        if position is not None:
            self.media_player.set_position(position)
        return self.media_player.get_position()

    def index(self) -> int | None:
        if self.media is None:
            return None
        return self.media_list.index_of_item(self.media)

    def next_identifier(self) -> str | None:
        if self.media is None:
            return None
        index = self.media_list.index_of_item(self.media)
        if index == self.media_list.count() - 1:
            return None
        return self.media_list.item_at_index(index + 1).get_mrl()

    def _media_from_to(self, start: int, end: int) -> Iterator[Media]:
        start = max(0, start)
        end = min(self.media_list.count()-1, end)
        if start >= self.media_list.count() or end < 0 or end < start:
            return
        for i in range(start, end+1):
            yield self.media_list.item_at_index(i)

    def identifiers_from_to(self, start: int, end: int) -> Iterator[str]:
        return map(lambda m: m.get_mrl(), self._media_from_to(start, end))

    def durations_from_to(self, start: int, end: int) -> Iterator[int]:
        for m in self._media_from_to(start, end):
            if m.get_parsed_status() != MediaParsedStatus.done:
                m.parse()
            yield m.get_duration()

    def size(self) -> int:
        return self.media_list.count()

    async def on_event(self) -> AsyncIterator[Player.Event]:
        async for event in self.async_events:
            yield event[0][0]
