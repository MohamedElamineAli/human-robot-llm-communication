from typing import Any
from datetime import datetime
import logging

from validator import ActionSchema, MemoryOperation, RobotPayload, ErrorPayload
from ..monitoring.logger import log_execution, log_safety_warning

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Dispatcher:

    def __init__(self, memory_store, robot_controller, feedback_interface):
        self.memory_store = memory_store
        self.robot_controller = robot_controller
        self.feedback = feedback_interface

    def dispatch(self, action: ActionSchema) -> Any:
        results = {
            "memory": None,
            "robot": None,
            "feedback": None,
            "error": None
        }

        if action.type == "error":
            results["error"] = self._handle_error(action.error)
            log_execution({"type": action.type}, results)
            return results

        if action.memory is not None:
            results["memory"] = self._handle_memory(action.memory)

        if action.robot is not None:
            results["robot"] = self._handle_robot(action.robot)

        if action.feedback is not None:
            results["feedback"] = self._handle_feedback(action.feedback)

        log_execution(action.model_dump(), results)
        return results

    def _handle_memory(self, mem_ops: list[MemoryOperation]) -> dict:
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
                log_safety_warning("MEMORY_OP_ERROR", f"Operation {op.operation} failed", {"operation": op.operation, "error": str(e)})
        return {"results": mem_results}

    def _handle_robot(self, robot_payload: RobotPayload) -> dict:
        try:
            for cmd in robot_payload.commands:
                self.robot_controller.execute(cmd.action, cmd.params)
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Robot commands execution failed")
            log_safety_warning("ROBOT_EXECUTION_ERROR", str(e), {"commands": robot_payload.commands})
            return {"status": "error", "error": str(e)}

    def _handle_feedback(self, feedback_message: str) -> dict:
        try:
            self.feedback.append(feedback_message)
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Feedback append failed")
            log_safety_warning("FEEDBACK_APPEND_ERROR", str(e), {"message": feedback_message})
            return {"status": "error", "error": str(e)}

    def _handle_error(self, error_payload: ErrorPayload) -> dict:
        logger.error("Error from action: code=%s message=%s", error_payload.code, error_payload.message)
        log_safety_warning("LLM_ERROR", error_payload.message, {"code": error_payload.code})
        return {"code": error_payload.code, "message": error_payload.message}