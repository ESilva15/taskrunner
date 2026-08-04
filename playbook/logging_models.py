from enum import StrEnum
from dataclasses import field
from pydantic import BaseModel
from datetime import datetime, timezone


class Status(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"


class LogTiming(BaseModel):
    start_date_timestamp: int = 0
    start_date: str = ""
    end_date: str = ""
    duration_sec: float = 0.0


class BaseLog(BaseModel):
    name: str
    timing: LogTiming = field(default=LogTiming())
    status: Status
    log_file_path: str = ""  # If set we have logged this particular step to a file


class ActLog(BaseLog):
    error: str = ""
    msg: str = ""
    logs: list[StepLogModel]

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, logs: list[StepLogModel], msg: str = "success") -> ActLog:
        return cls(name=name, status=Status.GOOD, msg=msg, logs=logs)

    @classmethod
    def fail(cls, name: str, err: str, logs: list[StepLogModel]) -> ActLog:
        return cls(name=name, status=Status.BAD, error=err, logs=logs)


class PlaybookLog(BaseLog):
    errors: list[str] = []
    summary: str = ""
    act_logs: list[ActLog]

    @property
    def failed(self) -> bool:
        return len(self.errors) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, logs: list[ActLog], msg: str = "success") -> PlaybookLog:
        return cls(name=name, status=Status.GOOD, summary=msg, act_logs=logs)

    @classmethod
    def fail(cls, name: str, logs: list[ActLog], err: list[str]) -> PlaybookLog:
        return cls(name=name, status=Status.BAD, errors=err, act_logs=logs)


class StepLogModel(BaseLog):
    error: str = ""
    msg: str = ""
    substeps_logs: list[StepLogModel] = []
    pipe_ctx: dict[str, object] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, msg: str = "success", pipe_ctx: dict[str, object] = {},
           substeps: list[StepLogModel] = []) -> StepLogModel:
        return cls(name=name, status=Status.GOOD, msg=msg, pipe_ctx=pipe_ctx,
                   substeps_logs=substeps)

    @classmethod
    def fail(cls, name: str, err: str) -> StepLogModel:
        return cls(name=name, status=Status.BAD, error=err)


def log_file_name(name: str, start_date_ns: int) -> str:
    """ Format to ISO 8601. """
    seconds = start_date_ns // 1_000_000_000
    ms = (start_date_ns % 1_000_000_000) // 1_000_000

    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()

    return dt.strftime(f"{name}_%Y-%m-%d_%H-%M-%S.{ms:03d}.log")
