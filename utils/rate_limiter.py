import time
from collections import defaultdict, deque
import asyncio


class RateLimiter:
    """
    Simple sliding-window rate limiter.
    Prevents a single clone from tripping Telegram's flood control
    when reacting to many messages quickly.
    """

    def __init__(self, max_calls: int, per_seconds: int = 60):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._history = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str):
        """
        Blocks (awaits) until a slot is free for the given key
        (key = clone_id or chat_id).
        """
        async with self._lock:
            now = time.monotonic()
            dq = self._history[key]

            while dq and now - dq[0] > self.per_seconds:
                dq.popleft()

            if len(dq) >= self.max_calls:
                wait_time = self.per_seconds - (now - dq[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._history[key].append(time.monotonic())
