from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QThread,
    pyqtSignal,
    QMutex,
    QWaitCondition,
    QMutexLocker,
)

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

    def __init__(
        self,
        main_window: MainWindow,
        max_stack_size: int = 256
    ):
        super().__init__()

        self._main_window = main_window
        self.max_stack_size = max_stack_size

        self.stack_trace: list[NodeStackFrame] = []

        self.current_node: BaseNode | None = None
        self._target_node: BaseNode | None = None

        self._running = False
        self._paused = False

        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()

        self.emit_event_signal.connect(self._safe_publish_event) # type: ignore

    # =========================================================
    # PUBLIC API
    # =========================================================

    @property
    def running(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._running


    @property
    def paused(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._paused

    def start_execution(self, start_node: BaseNode):
        with QMutexLocker(self._mutex):
            self._target_node = start_node

            if not self._running:
                self._running = True
                self._paused = False
                self.start()

            self._wait_condition.wakeAll()

    def request_stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
            self._paused = False
            self._target_node = None

            self._wait_condition.wakeAll()

    def request_pause(self):
        with QMutexLocker(self._mutex):
            if not self._running:
                return

            self._paused = True

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_PAUSED.value,
            source="NodeRunner",
            payload={}
        ))

    def request_resume(self):
        with QMutexLocker(self._mutex):
            if not self._running:
                return

            self._paused = False
            self._wait_condition.wakeAll()

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_RESUMED.value,
            source="NodeRunner",
            payload={}
        ))

    # =========================================================
    # THREAD LOOP
    # =========================================================

    def run(self):
        Debug.log_debug("NodeRunner thread started.")

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_STARTED.value,
            source="NodeRunner",
            payload={}
        ))

        while True:
            with QMutexLocker(self._mutex):

                while (
                    self._running and
                    (self._paused or self._target_node is None)
                ):
                    self._wait_condition.wait(self._mutex)

                if not self._running:
                    break

                node = self._target_node
                self._target_node = None

            if node is not None:
                self._execute_node(node)

        self._finish_internal()

    # =========================================================
    # EXECUTION
    # =========================================================

    def jump_to_node(
        self,
        target_node: BaseNode,
        via_socket: SocketItem
    ):
        with QMutexLocker(self._mutex):

            if not self._running:
                return

            self._target_node = target_node
            self._wait_condition.wakeAll()

    def fail(self, message: str = "Execution failed!"):
        Debug.log_error(message)
        self.request_stop()

    def _execute_node(self, node: BaseNode):
        Debug.log_debug(f"Executing node: {node.NODE_NAME}")

        self.current_node = node

        next_socket = node.execute()

        prev_node = self.stack_trace[-1].node if self.stack_trace else None

        edge = None

        if prev_node:
            for out_sock in prev_node.exec_outputs:
                for e in out_sock.edges:
                    if (
                        e.start_socket.parent_node == prev_node
                        and e.end_socket is not None
                        and e.end_socket.parent_node == node
                    ):
                        edge = e
                        break

                if edge:
                    break

        self.stack_trace.append(
            NodeStackFrame(node, edge_from=edge)
        )

        if len(self.stack_trace) > self.max_stack_size:
            self.stack_trace.pop(0)

        if next_socket is None or not next_socket.is_exec:
            if next_socket is not None and not next_socket.is_exec:
                Debug.log_error(f"Node '{node.NODE_NAME}' did not return a valid execution socket.")
            self.request_stop()
            return

        next_node = None

        for edge_item in next_socket.edges:
            if (
                edge_item.start_socket == next_socket
                and edge_item.end_socket is not None
            ):
                next_node = edge_item.end_socket.parent_node
                break

        if next_node:
            self.jump_to_node(next_node, next_socket)
        else:
            self.request_stop()

    # =========================================================
    # INTERNAL
    # =========================================================

    def _safe_publish_event(self, event_obj: Event):
        self._main_window.event_bus.publish(event_obj)

    def _finish_internal(self):
        Debug.log_debug("NodeRunner execution finished.")

        self.emit_event_signal.emit(Event(
            type=EventType.EVENT_EXECUTION_STOPPED.value,
            source="NodeRunner",
            payload={}
        ))