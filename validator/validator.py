from typing import Dict, Any, List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

class MemoryOperation(BaseModel):
    operation: Literal["append", "deactivate", "edit", "reactivate", "archive"]
    data: Optional[str] = None
    id: Optional[str] = None
    time: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_fields_by_operation(self):
        op = self.operation
        
        # Check data requirement
        if op in ("append", "edit") and self.data is None:
            raise ValueError(f"data is required when operation is '{op}'")
        
        # Check id requirement  
        if op in ("deactivate", "edit", "reactivate") and self.id is None:
            raise ValueError(f"id is required when operation is '{op}'")
        
        # Check time requirement
        if self.time is None:
            raise ValueError("time must be provided in MemoryOperation")
            
        return self

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
    def check_required_by_type(self):
        t = self.type
        if t == "memory":
            if self.memory is None:
                raise ValueError("memory field required when type='memory'")
        if t == "robot":
            if self.robot is None:
                raise ValueError("robot field required when type='robot'")
        if t == "monitor":
            if self.monitor is None:
                raise ValueError("monitor field required when type='monitor'")
        if t == "error":
            if self.error is None:
                raise ValueError("error field required when type='error'")
        if t == "combo":
            if not any([self.memory is not None, self.robot is not None, self.monitor is not None]):
                raise ValueError("combo requires at least one of memory, robot, or monitor fields")
        if t == "all":
            if not all([self.memory is not None, self.robot is not None, self.monitor is not None]):
                raise ValueError("all requires memory, robot, and monitor fields")
        return self

def validate_action(payload: Dict[str, Any]) -> ActionSchema:
    return ActionSchema.model_validate(payload)

if __name__ == "__main__":
    good = {
        "type": "memory",
        "memory": [
            {
                "operation": "append",
                "data": "some string data",
                "id": "123",
                "time": "2025-09-20T15:30:00Z"
            }
        ]
    }

    bad1 = {
        "type": "memory",
        "memory": [
            {
                "operation": "append",  # requires data
                "id": "123",
                "time": "2025-09-20T15:30:00Z"
                # missing data field
            }
        ]
    }

    bad2 = {
        "type": "memory",
        "memory": [
            {
                "operation": "deactivate",  # requires id
                "time": "2025-09-20T15:30:00Z"
                # missing id field
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