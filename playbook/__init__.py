from __future__ import annotations

import json
import datetime
from os import error, name
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum, StrEnum


class Status(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"


@dataclass
class StepLog(object):
    step_name: str
    status: Status
    duration_sec: int
    msg: str
    error: List[str] = field(default_factory=list)
    substeps: List[StepLog] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        """ Checks if the step failed """
        return len(self.error) > 0 or self.status == Status.BAD


# # NOTE: maybe shoulnd't have used an enum
# class StepLogEncoder(json.JSONEncoder):
#     """ JSON Encoder for Status Enums. """
#     def default(self, o):
#         if isinstance(o, Status):
#             return o.name
#         return super().default(o)


class StepIF(ABC):
    """ Interface for plays. """

    @abstractmethod
    def pre(self) -> StepLog:
        """ Run at the start to validate the configurations, inputs, etc. """
        pass
    
    @abstractmethod
    def play(self) -> StepLog:
        """ Steps to actually run the backup. """

    @abstractmethod
    def post(self) -> StepLog:
        """ Run at the end to validate the actions made. """

    def run(self, name: str) -> StepLog:
        """ Run the step. """
        start_time: float = datetime.datetime.now().timestamp()

        substeps: List[StepLog] = []
        status: Status = Status.GOOD
        for op in [self.pre, self.play, self.post]:
            log: StepLog = op()
            status = Status.BAD if log.failed else Status.GOOD

            substeps.append(log)

            if status == Status.BAD:
                break

        end_time: float = datetime.datetime.now().timestamp()
        delta: int = int(end_time - start_time)
         
        errors = []
        msg: str = ""
        if status == Status.BAD:
            errors = ["substep failed"]
        else:
            msg = "success"

        return StepLog(
                step_name=name, status=status, duration_sec=delta,
                msg=msg, error=errors, substeps=substeps,
                )


class CustomStep(StepIF):
    """ Pre made play to backup directories. """

    def __init__(
        self, 
        name: str,
        pre_fn: Callable[[Dict[str, Any]], StepLog],
        play_fn: Callable[[Dict[str, Any]], StepLog],
        post_fn: Callable[[Dict[str, Any]], StepLog],
    ):
        self.name: str = name

        self.pre_fn = pre_fn
        self.play_fn = play_fn
        self.post_fn = post_fn

        self.__context: Dict[str, Any] = {}

    def pre(self) -> StepLog:
        return self.pre_fn(self.__context)
    
    def play(self) -> StepLog:
        return self.play_fn(self.__context)

    def post(self):
        return self.post_fn(self.__context)


@dataclass
class StepEntry(object):
    name: str
    step: StepIF


class Play(object):
    def __init__(self, name : str):
        self.name: str = name
        self.__steps: List[StepEntry] = []

    def add_step(self, name: str, stepRunner : StepIF):
        self.__steps.append(StepEntry(name=name, step=stepRunner))

    def view_playbook(self) -> str:
        steps: List[str] = []
        for s in self.__steps:
            steps.append(s.name)

        data = {
            "name": self.name,
            "number_of_steps": len(steps),
            "steps": steps,
        }

        return json.dumps(data)

    def play(self) -> StepLog:
        start_time: float = datetime.datetime.now().timestamp()
        playLog: StepLog = StepLog(
                step_name=self.name,
                status=Status.GOOD,
                duration_sec=0,
                msg="",
                error=[],
                substeps=[],
                )

        for s in self.__steps:
            log: StepLog = s.step.run(s.name)

            playLog.substeps.append(log)

            if log.failed:
                playLog.error.append(f"failed in step: {s.name}")
                playLog.status = Status.BAD
                break

        end_time: float = datetime.datetime.now().timestamp()
        delta: int = int(end_time - start_time)
        playLog.duration_sec = delta

        if playLog.status == Status.GOOD:
            playLog.msg = "success"

        return playLog


class Service(object):
    def __init__(self, name: str): 
        self.name = name
        self.__playbook: List[StepIF] = []

    @classmethod
    def run(cls):
        pass


