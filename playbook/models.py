import time
from enum import StrEnum
from typing import List, Dict, Any, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field


class Status(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"


@dataclass
class StepLog(object):
    step_name: str
    status: Status = Status.BAD  # By default set it to bad so the it fails by default
                                 # The user needs to be explicit
    cmd: str = ""
    start_date_timestamp: int = 0
    start_date: str = ""
    end_date: str = ""
    duration_sec: float = 0.0
    human_readable_duration: str = ""
    msg: str = ""
    error: List[Dict[Any, Any]] = field(default_factory=list)
    substeps: List[StepLog] = field(default_factory=list)
    log_file_path: str = ""

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, msg: str = "success") -> StepLog:
        return cls(step_name=name, status=Status.GOOD, msg=msg)

    @classmethod
    def fail(cls, name: str, errors: List[Any]) -> StepLog:
        return cls(step_name=name, status=Status.BAD, error=errors)


def human_readable_date(time: int) -> str:
    seconds = time // 1_000_000_000
    nanos = time % 1_000_000_000

    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()

    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{nanos:09d}%:z")


def timed_run(op: Callable[..., StepLog], *args: Any, **kwargs: Any) -> StepLog:
    start_date: int = time.time_ns()
    start_time: int = time.perf_counter_ns()
    
    try:
        log: StepLog = op(*args, **kwargs)
    finally:
        delta = time.perf_counter_ns() - start_time
    
    # NOTE: we could simplyfy this by having a marshalling method
    if isinstance(log, StepLog):
        end_date: int = time.time_ns()
        log.duration_sec = delta / 1_000_000_000.0
        log.start_date = human_readable_date(start_date)
        log.start_date_timestamp = start_date
        log.end_date = human_readable_date(end_date)
    
    return log
