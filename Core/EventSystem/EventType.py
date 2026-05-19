from enum import Enum

class EventType(Enum):
    EVENT_VARIABLE_UPDATED = "event_variable_updated"
    EVENT_VARIABLE_ADDED = "event_variable_added"
    EVENT_VARIABLE_REMOVED = "event_variable_removed"

    EVENT_NODE_ADDED = "event_node_added"
    EVENT_NODE_REMOVED = "event_node_removed"

    EVENT_LOG_ADDED = "event_log_added"

    EVENT_EXECUTION_STARTED = "event_execution_started"
    EVENT_EXECUTION_PAUSED = "event_execution_paused"
    EVENT_EXECUTION_RESUMED = "event_execution_resumed"
    EVENT_EXECUTION_STOPPED = "event_execution_stopped"