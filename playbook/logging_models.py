from enum import StrEnum
from dataclasses import field
from pydantic import BaseModel


class Status(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"


class LogTiming(BaseModel):
    start_date_timestamp: int = 0
    start_date: str = ""
    end_date: str = ""
    duration_sec: float = 0.0


class StepLogModel(BaseModel):
    name: str
    timing: LogTiming = field(default=LogTiming())
    status: Status
    error: str = ""
    msg: str = ""
    pipe_ctx: dict[str, object] = field(default_factory=dict)
    log_file_path: str = ""  # If set we have logged this particular step to a file

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, msg: str = "success", pipe_ctx: dict[str, object] = {}) -> StepLogModel:
        return cls(name=name, status=Status.GOOD, msg=msg, pipe_ctx=pipe_ctx)

    @classmethod
    def fail(cls, name: str, err: str) -> StepLogModel:
        return cls(name=name, status=Status.BAD, error=err)
