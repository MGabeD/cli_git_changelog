import threading
import time
from queue import Queue, Empty
from concurrent.futures import Future
from typing import Callable, Any, Tuple, Optional


class RateLimitedTaskDispatcher:
    def __init__(self, max_calls: int, period_sec: float, idle_timeout: float = 10.0):
        """
        :param max_calls: number of allowed calls per period
        :param period_sec: the length of the period in seconds
        :param idle_timeout: how long to wait before auto-shutdown when queue is empty
        """
        self.period_per_call = period_sec / max_calls
        self.idle_timeout = idle_timeout
        self.queue: Queue[Tuple[Callable, Tuple[Any, ...], dict, Future]] = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self._shutdown_event = threading.Event()

    def _start_worker_if_needed(self):
        with self.lock:
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self._shutdown_event.clear()
                self.worker_thread = threading.Thread(target=self._run, daemon=True)
                self.worker_thread.start()

    def _run(self):
        while not self._shutdown_event.is_set():
            try:
                fn, args, kwargs, future = self.queue.get(timeout=self.idle_timeout)
            except Empty:
                self._shutdown_event.set()
                break

            try:
                result = fn(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

            time.sleep(self.period_per_call)

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        future = Future()
        self.queue.put((fn, args, kwargs, future))
        self._start_worker_if_needed()
        return future
