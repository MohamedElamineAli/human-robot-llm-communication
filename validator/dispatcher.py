# dispatcher.py

from typing import Any
from datetime import datetime
import logging

from validator import ActionSchema, MemoryOperation, RobotPayload, ErrorPayload

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Dispatcher:

    def __init__(self, memory_store, robot_controller, monitor_interface):
        self.memory_store = memory_store
        self.robot_controller = robot_controller
        self.monitor = monitor_interface

    def dispatch(self, action: ActionSchema) -> Any:
        results = {
            "memory": None,
            "robot": None,
            "monitor": None,
            "error": None
        }

        if action.type == "error":
            results["error"] = self._handle_error(action.error)
            return results

        if action.memory is not None:
            results["memory"] = self._handle_memory(action.memory)

        if action.robot is not None:
            results["robot"] = self._handle_robot(action.robot)

        if action.monitor is not None:
            results["monitor"] = self._handle_monitor(action.monitor)

        return results

    def _handle_memory(self, mem_ops: list[MemoryOperation]) -> dict:
        """
        Apply each memory operation in sequence.
        """
        mem_results = []
        for op in mem_ops:
            try:
                if op.operation == "append":
                    rec = {
                        "data": op.data,
                        "time": op.time or datetime.utcnow().isoformat(),
                        "is_active": True
                    }
                    inserted_id = self.memory_store.append(rec)
                    mem_results.append({"operation": "append", "status": "ok", "new_id": inserted_id})
                elif op.operation == "deactivate":
                    assert op.id is not None
                    self.memory_store.deactivate(op.id)
                    mem_results.append({"operation": "deactivate", "status": "ok", "id": op.id})
                elif op.operation == "edit":
                    # edit == deactivate old and append new
                    assert op.id is not None and op.data is not None
                    self.memory_store.deactivate(op.id)
                    rec = {
                        "data": op.data,
                        "time": op.time or datetime.utcnow().isoformat(),
                        "is_active": True
                    }
                    new_id = self.memory_store.append(rec)
                    mem_results.append({"operation": "edit", "status": "ok", "old_id": op.id, "new_id": new_id})
                elif op.operation == "reactivate":
                    assert op.id is not None
                    self.memory_store.reactivate(op.id)
                    mem_results.append({"operation": "reactivate", "status": "ok", "id": op.id})
                elif op.operation == "archive":
                    self.memory_store.archive()
                    mem_results.append({"operation": "archive", "status": "ok"})
                else:
                    mem_results.append({"operation": op.operation, "status": "unknown_operation"})
            except Exception as e:
                logger.exception("Memory operation failed: %s", op)
                mem_results.append({"operation": op.operation, "status": "error", "error": str(e)})
        return {"results": mem_results}

    def _handle_robot(self, robot_payload: RobotPayload) -> dict:
        """
        Send robot commands for execution.
        """
        try:
            for cmd in robot_payload.commands:
                self.robot_controller.execute(cmd.action, cmd.params)
                
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Robot commands execution failed")
            return {"status": "error", "error": str(e)}

    def _handle_monitor(self, monitor_message: str) -> dict:
        try:
            self.monitor.notify(monitor_message)
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Monitor notification failed")
            return {"status": "error", "error": str(e)}

    def _handle_error(self, error_payload: ErrorPayload) -> dict:
        logger.error("Error from action: code=%s message=%s", error_payload.code, error_payload.message)
        return {"code": error_payload.code, "message": error_payload.message}

