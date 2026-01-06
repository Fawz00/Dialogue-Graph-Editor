from enum import Enum

class EventType(Enum):
    EVENT_VARIABLE_UPDATED = "event_variable_updated"
    EVENT_VARIABLE_ADDED = "event_variable_added"
    EVENT_VARIABLE_REMOVED = "event_variable_removed"

    EVENT_NODE_ADDED = "event_node_added"
    EVENT_NODE_REMOVED = "event_node_removed"

    EVENT_LOG_ADDED = "event_log_added"