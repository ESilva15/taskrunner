from __future__ import annotations

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
    pipe_ctx: Dict[str, Any] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD

    @classmethod
    def ok(cls, name: str, msg: str = "success", pipe_ctx: Dict[str, Any] = {}) -> StepLog:
        return cls(step_name=name, status=Status.GOOD, msg=msg, pipe_ctx=pipe_ctx)

    @classmethod
    def fail(cls, name: str, errors: List[Any]) -> StepLog:
        return cls(step_name=name, status=Status.BAD, error=errors)


class ContextChecker:
    """Safely extract values with error messages."""
    def __init__(self, ctx: Dict[str, Any]):
        self._ctx = ctx

    @classmethod
    def requires(cls, *args):
        def decorator(func: ActionFn):
            def wrapper(ctx: Dict[str, Any], name: str) -> StepLog:
                if all(key in ctx for key in args):
                    return func(ctx, name)
                else:
                    missing_keys = [key for key in args if key not in ctx]
                    missing_keys_msg = f"missing context keys: {missing_keys}"
                    return StepLog.fail(name, [{"status": "failed", "output": missing_keys_msg}])
            return wrapper
        return decorator


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


ActionFn = Callable[[Dict[str, Any], str], StepLog]
