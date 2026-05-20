from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

from Core.Debug.Debug import Debug
from Core.EventSystem.Event import Event
from Core.EventSystem.EventType import EventType
from Core.Graph.EdgeItem import EdgeItem

if TYPE_CHECKING:
    from Main import MainWindow
    from Core.Graph.BaseNode import BaseNode
    from Core.Graph.SocketItem import SocketItem

class NodeStackFrame:
    def __init__(self, node: BaseNode, edge_from: EdgeItem | None = None):
        self.node = node
        self.edge_from = edge_from

class NodeRunner(QThread):
    emit_event_signal = pyqtSignal(object) 

    # Tambahkan parameter max_stack_size di __init__
    def __init__(self, main_window: MainWindow, max_stack_size: int = 256):
        super().__init__() 
        self._main_window = main_window
        
        self.max_stack_size = max_stack_size

        self.is_running = False
        self.is_paused = False
        self.stack_trace: list[NodeStackFrame] = []
        self.current_node: BaseNode | None = None
        
        self._target_node: BaseNode | None = None

        self.emit_event_signal.connect(self._safe_publish_event) # type: ignore

    def start_execution(self, start_node: BaseNode):
        if self.is_running and not self.is_paused:
            Debug.log_warning("NodeRunner is already running!")
            return

        Debug.log_debug("NodeRunner starting execution.")
        
        self._target_node = start_node
        self.start()
    
    def request_resume(self):
        if not self.is_running or not self.is_paused:
            return

        Debug.log_debug("NodeRunner resume requested.")
        self.is_paused = False

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_RESUMED.value,
            source="NodeRunner",
            payload={}
        ))

    # Qt threading requires the run method to be defined for the thread's activity
    def run(self):
        self.is_running = True
        self.is_paused = False
        self.stack_trace.clear()

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_STARTED.value,
            source="NodeRunner",
            payload={}
        ))

        while self.is_running:
            if self.is_paused:
                self.msleep(10)
                continue

            if self._target_node is None:
                self.msleep(1)
                continue

            node = self._target_node
            self._target_node = None

            self.current_node = node
            self._execute_node(node)

            self.msleep(1)

        self._finish()

    def request_stop(self):
        if not self.is_running:
            return
        Debug.log_debug("NodeRunner stop requested.")
        self._finish()
    
    def request_pause(self):
        if not self.is_running:
            return
        Debug.log_debug("NodeRunner pause requested.")
        self.is_paused = True 

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_PAUSED.value,
            source="NodeRunner",
            payload={}
        ))



    #region JUMP
    def jump_to_node(self, target_node: BaseNode, via_socket: SocketItem):
        if not self.is_running: return

        if via_socket:
            valid_jump = False
            for edge in via_socket.edges:
                if edge.start_socket.parent_node == self.current_node and edge.end_socket is not None and edge.end_socket.parent_node == target_node:
                    valid_jump = True
                    break
            if not valid_jump:
                node_name = self.current_node.title if self.current_node else "None"
                self.fail(f"Invalid jump: No edge from {node_name} to {target_node.title} via socket {via_socket}")
                return
        
        self._target_node = target_node
    #endregion JUMP

    #region FAIL
    def fail(self, message: str = "Execution failed!"):
        Debug.log_error(f"Execution failed: {message}")
        self._finish()
    #endregion FAIL



    #region Helper Methods
    def _safe_publish_event(self, event_obj: Event) -> None:
        self._main_window.event_bus.publish(event_obj)

    def _execute_node(self, node: BaseNode):
        if not self.is_running:
            return

        Debug.log_debug(f"Executing node: {node.title}")
        self.current_node = node
        next_socket: SocketItem | None = node.execute()

        prev_node = self.stack_trace[-1].node if self.stack_trace else None
        edge: EdgeItem | None = None
        if prev_node:
            for out_sock in prev_node.outputs:
                for e in out_sock.edges:
                    if e.start_socket.parent_node == prev_node and e.end_socket is not None and e.end_socket.parent_node == node:
                        edge = e
                        break
                if edge: break

        self.stack_trace.append(NodeStackFrame(node, edge_from=edge))
        
        # --- PERBAIKAN: Limitasi Stack Trace agar terhindar dari Memory Leak ---
        if len(self.stack_trace) > self.max_stack_size:
            self.stack_trace.pop(0) # Buang history yang paling tua (index 0)

        if next_socket and next_socket.is_exec:
            next_node = None
            for edge_item in next_socket.edges:
                if edge_item.start_socket == next_socket and edge_item.end_socket is not None:
                    next_node = edge_item.end_socket.parent_node
                    break
            
            if next_node:
                self.jump_to_node(next_node, next_socket)
            else:
                self._finish() 
        else:
            self._finish() 
    
    def _finish(self):
        already_stopped = not self.is_running

        self._target_node = None
        self.is_running = False
        self.is_paused = False

        if already_stopped:
            return

        Debug.log_debug("NodeRunner execution finished.")

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_STOPPED.value,
            source="NodeRunner",
            payload={}
        ))
    #endregion Helper Methods