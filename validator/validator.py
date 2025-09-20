from typing import Dict, Any, List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class MemoryOperation(BaseModel):
    operation: Literal["append", "deactivate", "edit", "reactivate", "archive"]
    data: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    time: Optional[datetime] = None

    # Field-level validation for MemoryOperation
    @field_validator("data", mode="after")
    @classmethod
    def data_required_for_append_or_edit(cls, v: Optional[Dict[str, Any]], info):
        op = info.data.get("operation")
        if op in ("append", "edit"):
            if v is None:
                raise ValueError(f"'data' is required when operation is '{op}'")
        return v

    @field_validator("id", mode="after")
    @classmethod
    def id_required_for_non_append(cls, v: Optional[str], info):
        op = info.data.get("operation")
        if op in ("deactivate", "edit", "reactivate"):
            if v is None:
                raise ValueError(f"'id' is required when operation is '{op}'")
        return v

    @field_validator("time", mode="after")
    @classmethod
    def time_required_for_all(cls, v: Optional[datetime], info):
        # If you want time always required (or at least in some ops), you can adjust.
        if v is None:
            raise ValueError("'time' must be provided in MemoryOperation")
        return v


class RobotCommand(BaseModel):
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)


class RobotPayload(BaseModel):
    commands: List[RobotCommand]
    min_runtime_sec: int = Field(..., ge=0)


class ErrorPayload(BaseModel):
    code: str
    message: str


class ActionSchema(BaseModel):
    type: Literal["memory", "robot", "monitor", "combo", "all", "error"]
    memory: Optional[List[MemoryOperation]] = None
    robot: Optional[RobotPayload] = None
    monitor: Optional[str] = None
    error: Optional[ErrorPayload] = None

    @model_validator(mode="after")
    def check_required_by_type(cls, model) -> "ActionSchema":
        t = model.type
        if t == "memory":
            if model.memory is None:
                raise ValueError("Field 'memory' is required when type='memory'")
        if t == "robot":
            if model.robot is None:
                raise ValueError("Field 'robot' is required when type='robot'")
        if t == "monitor":
            if model.monitor is None:
                raise ValueError("Field 'monitor' is required when type='monitor'")
        if t == "error":
            if model.error is None:
                raise ValueError("Field 'error' is required when type='error'")
        if t == "combo":
            # at least one of memory, robot, monitor
            if not any([model.memory is not None, model.robot is not None, model.monitor is not None]):
                raise ValueError("Type 'combo' requires at least one of memory, robot, or monitor fields")
        if t == "all":
            if not all([model.memory is not None, model.robot is not None, model.monitor is not None]):
                raise ValueError("Type 'all' requires memory, robot, and monitor fields")
        return model


def validate_action(payload: Dict[str, Any]) -> ActionSchema:
    """
    Validate action schema, using Pydantic v2's model_validate.
    Raises ValidationError if invalid.
    """
    return ActionSchema.model_validate(payload)


# Example tests:
if __name__ == "__main__":
    # Example that should succeed
    good = {
        "type": "memory",
        "memory": [
            {
                "operation": "append",
                "data": {"foo": "bar"},
                "id": "123",
                "time": "2025-09-20T15:30:00Z"
            }
        ]
    }

    # Example that should fail: missing data in append
    bad1 = {
        "type": "memory",
        "memory": [
            {
                "operation": "append",
                # "data" missing
                "id": "123",
                "time": "2025-09-20T15:30:00Z"
            }
        ]
    }

    # Example that should fail: missing id in deactivate
    bad2 = {
        "type": "memory",
        "memory": [
            {
                "operation": "deactivate",
                "time": "2025-09-20T15:30:00Z"
            }
        ]
    }

    try:
        v = validate_action(good)
        print("Good validated:", v.model_dump_json(indent=2))
    except ValidationError as e:
        print("Good failed:", e)

    try:
        v = validate_action(bad1)
        print("Bad1 validated:", v.model_dump_json(indent=2))
    except ValidationError as e:
        print("Bad1 failed:", e)

    try:
        v = validate_action(bad2)
        print("Bad2 validated:", v.model_dump_json(indent=2))
    except ValidationError as e:
        print("Bad2 failed:", e)