from __future__ import annotations

import yaml
import time
import functools
from typing import Callable
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator

from playbook.action_registry import ActionRegistry, ActionFn
from playbook.logging_models import StepLogModel


class StepModel(BaseModel):
    name: str
    _actions: list[ActionFn]
    _context: dict[str, object]

    def get_action_names(self) -> list[str]:
        return [action.__name__ for action in self._actions]

    # NOTE: refactor this method to be more readable
    def run(self, ctx) -> StepLogModel:
        """ Run the step. """
        return StepLogModel.ok(self.name, msg="success")
        # substeps: list[StepLogModel] = []
        # status: Status = Status.GOOD
        #
        # # NOTE:
        # # Use this to move context from the previous step to the next step
        # # This is wrong, we are moving away from having a list of steps here to a single
        # # step for each operation
        # prev_step_ctx: dict[str, object] = {}
        #
        # for op in self.__actions:
        #     try:
        #         log: StepLogModel = timed_run(
        #             op, ctx | prev_step_ctx | self.__context, self.name)
        #     except Exception as e:
        #         log: StepLogModel = StepLogModel.fail(
        #             self.name, [{"status": "failed", "output": str(e)}])
        #
        #     status = Status.BAD if log.failed else Status.GOOD
        #     prev_step_ctx = log.pipe_ctx
        #
        #     substeps.append(log)
        #
        #     if status == Status.BAD:
        #         break
        #
        # errors = []
        # msg: str = ""
        # if status == Status.BAD:
        #     # Note, use this to set the standar error output/formatting
        #     # errors = [{"status": "failed", "output": ""}]
        #     errors = []
        # else:
        #     msg = "success"
        #
        # return StepLogModel(
        #     step_name=self.name, status=status,
        #     msg=msg, error=errors, substeps=substeps, pipe_ctx=prev_step_ctx
        # )


class ActModel(BaseModel):
    name: str
    steps: list[StepModel]

    # NOTE: this shouldnt return a steplogmodel but an actlogmodel or something like that
    def run(self, ctx) -> StepLogModel:
        return StepLogModel.ok(self.name, msg="success")


class PlaybookModel(BaseModel):
    playbook_name: str
    log_dir: str
    registries: list[ActionRegistry]
    global_context: dict[str, str]
    acts: list[ActModel]

    @field_validator("registries", mode="before")
    @classmethod
    def parse_registries(cls, v: object) -> list[ActionRegistry]:
        result = []
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    try:
                        registries: list[ActionRegistry] = \
                            ActionRegistry.load_registries_from_file(item)
                        result.extend(registries)
                    except Exception as e:
                        raise e
                else:
                    raise ValueError(f"Invalid registry type: {type(item)}")
        return result

    @classmethod
    def from_yaml_file(cls, fp: str):
        with open(fp, "rb") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def _run(self) -> StepLogModel:
        for act in self.acts:
            act.run(self.global_context)

        return StepLogModel.ok(name="somasjd", msg="ajshdsajhd")

    def run(self) -> StepLogModel:
        return timed_run(self._run)


class ContextChecker:
    """Safely extract values with error messages."""

    def __init__(self, ctx: dict[str, object]):
        self._ctx = ctx

    @classmethod
    def requires(cls, *args):
        def decorator(func: ActionFn):
            @functools.wraps(func)
            def wrapper(ctx: dict[str, object], name: str) -> StepLogModel:
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


def timed_run(op: Callable[..., StepLogModel], *args: object, **kwargs: object) -> StepLogModel:
    start_date: int = time.time_ns()
    start_time: int = time.perf_counter_ns()

    try:
        log: StepLogModel = op(*args, **kwargs)
    finally:
        delta = time.perf_counter_ns() - start_time

    # NOTE: we could simplyfy this by having a marshalling method
    if isinstance(log, StepLogModel):
        end_date: int = time.time_ns()
        log.timing.duration_sec = delta / 1_000_000_000.0
        log.timing.start_date = human_readable_date(start_date)
        log.timing.start_date_timestamp = start_date
        log.timing.end_date = human_readable_date(end_date)

    return log
