import threading
from typing import Dict

_events: Dict[str, threading.Event] = {}
_lock = threading.Lock()


def register(process_id: str) -> threading.Event:
    with _lock:
        event = threading.Event()
        event.set()  # set = running, clear = paused
        _events[process_id] = event
        return event


def pause(process_id: str) -> None:
    with _lock:
        if process_id in _events:
            _events[process_id].clear()


def resume(process_id: str) -> None:
    with _lock:
        if process_id in _events:
            _events[process_id].set()


def unregister(process_id: str) -> None:
    with _lock:
        _events.pop(process_id, None)
