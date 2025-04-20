import threading
import time
from queue import Queue
from concurrent.futures import Future
from typing import Callable
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


class RateLimitedTaskDispatcher:
    def __init__(self, capacity: int, refill_interval: float, idle_timeout: float = 10.0):
        """
        :param capacity: max number of allowed calls per time window
        :param refill_interval: how often to refill one token (e.g., 60 / 50 = 1.2s)
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_interval = refill_interval
        self.token_lock = threading.Lock()

        self.queue = Queue()
        self.idle_timeout = idle_timeout
        self._shutdown_event = threading.Event()
        self.dispatcher_thread = threading.Thread(target=self._run, daemon=True)
        self.refiller_thread = threading.Thread(target=self._refill, daemon=True)

        self.dispatcher_thread.start()
        self.refiller_thread.start()

    def _refill(self):
        while not self._shutdown_event.is_set():
            with self.token_lock:
                if self.tokens < self.capacity:
                    self.tokens += 1
            time.sleep(self.refill_interval)

    def _consume_token(self) -> bool:
        with self.token_lock:
            if self.tokens > 0:
                self.tokens -= 1
                return True
            logger.warn("Rate limited, no tokens available WAITING")
            return False

    def _run(self):
        while not self._shutdown_event.is_set():
            try:
                fn, args, kwargs, future = self.queue.get(timeout=self.idle_timeout)
            except Exception:
                self._shutdown_event.set()
                break

            while not self._consume_token():
                time.sleep(0.1)

            try:
                result = fn(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        future = Future()
        self.queue.put((fn, args, kwargs, future))
        return future