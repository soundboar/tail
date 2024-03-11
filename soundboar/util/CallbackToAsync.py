# Adapted from https://github.com/multimeric/Asynchronize/blob/master/asynchronize/__init__.py
import asyncio


class MakeAsync:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.finished = False
        self.loop = asyncio.get_event_loop()

    def event(self, *args, **kwargs):
        # Whenever a step is called, add to the queue but don't set finished to True, so __anext__ will continue
        args = (args, kwargs)

        # We have to use the threadsafe call so that it wakes up the event loop, in case it's sleeping:
        # https://stackoverflow.com/a/49912853/2148718
        self.loop.call_soon_threadsafe(
            self.queue.put_nowait,
            args
        )

    def finish(self):
        self.finished = True

    def __await__(self):
        # Since this implements __anext__, this can return itself
        return self.queue.get().__await__()

    def __aiter__(self):
        # Since this implements __anext__, this can return itself
        return self

    async def __anext__(self):
        # Keep waiting for the queue if a) we haven't finished, or b) if the queue is still full. This lets us finish
        # processing the remaining items even after we've finished
        if self.finished and self.queue.empty():
            raise StopAsyncIteration

        return await self.queue.get()
