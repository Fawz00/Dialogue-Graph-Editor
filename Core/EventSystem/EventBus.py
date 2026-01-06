from collections import defaultdict
from typing import Callable, List

from Core.EventSystem.Event import Event

class EventBus:
    def __init__(self):
        self._listeners: dict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def publish(self, event: Event):
        # Specific listeners
        for callback in self._listeners.get(event.type, []):
            callback(event)

        # Wildcard listeners (logging, debugger, recorder)
        for callback in self._listeners.get("*", []):
            callback(event)
