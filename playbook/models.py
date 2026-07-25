from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Callable, Dict, List, Any


class Status(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"


@dataclass
class StepLog(object):
    step_name: str
    status: Status = Status.BAD  # By default set it to bad so the it fails by default
                                 # The user needs to be explicit
    duration_sec: int = 0
    msg: str = ""
    error: List[str] = field(default_factory=list)
    substeps: List[StepLog] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD


