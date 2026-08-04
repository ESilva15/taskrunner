from __future__ import annotations

import yaml
import time
import functools
from typing import Callable
from datetime import datetime, timezone
from pydantic import BaseModel, ValidationInfo, field_serializer, field_validator, model_validator

from playbook.action_registry import ActionRegistry, ActionFn
from playbook.logging_models import PlaybookLog, StepLogModel, ActLog, Status


CtxType = dict[str, object]


class StepModel(BaseModel):
    name: str
    action: ActionFn
    context: dict[str, object]

    @field_serializer("action")
    def serialize_action_fn(self, action_fn: ActionFn, _info) -> str:
        return getattr(action_fn, "__name__", str(action_fn))

    def run(self, ctx: dict[str, object]) -> StepLogModel:
        """ Run the step. """
        substeps: list[StepLogModel] = []
        previous_step_ctx: dict[str, object] = {}

        try:
            local_ctx: CtxType = ctx | previous_step_ctx | self.context
            log: StepLogModel = timed_run(
                self.action, local_ctx, self.name
            )
        except Exception as e:
            log: StepLogModel = StepLogModel.fail(
                self.name, str(e)
            )

        previous_step_ctx = log.pipe_ctx

        substeps.append(log)
        if log.status == Status.BAD:
            return StepLogModel.fail(self.name, err=f"failed on step: {log.name}")

        return StepLogModel.ok(self.name, msg="success", substeps=substeps)


class ActModel(BaseModel):
    name: str
    steps: list[StepModel]

    # NOTE: this shouldnt return a steplogmodel but an actlogmodel or something like that
    def run(self, ctx) -> ActLog:
        step_logs: list[StepLogModel] = []
        for step in self.steps:
            stepLog: StepLogModel = timed_run(step.run, ctx)
            step_logs.append(stepLog)
            if stepLog.failed:
                break

        return ActLog.ok(self.name, msg="success", logs=step_logs)


class PlaybookModel(BaseModel):
    playbook_name: str
    log_dir: str
    registries: list[ActionRegistry]
    global_context: dict[str, str]
    acts: list[ActModel]

    @model_validator(mode="before")
    @classmethod
    # def parse_registries(cls, v: object) -> list[ActionRegistry]:
    def load_registries(cls, data: object, info: ValidationInfo) -> object:
        if not isinstance(data, dict):
            return data

        raw_registries = data.get("registries", [])
        loaded_registries: list[ActionRegistry] = []

        for item in raw_registries:
            if isinstance(item, str):
                loaded_registries.extend(ActionRegistry.load_registries_from_file(item))

        data["registries"] = loaded_registries

        if info.context is not None:
            info.context["registries"] = loaded_registries

        return data

    @classmethod
    def from_yaml_file(cls, fp: str):
        with open(fp, "rb") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data, context={})
        # return cls(**data)

    def _run(self) -> PlaybookLog:
        act_logs: list[ActLog] = []
        for act in self.acts:
            log: ActLog = timed_run(act.run, self.global_context)
            act_logs.append(log)

        return PlaybookLog.ok(name="somasjd", msg="ajshdsajhd", logs=act_logs)

    def run(self) -> PlaybookLog:
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
                    return StepLogModel.fail(name, err=missing_keys_msg)
            return wrapper
        return decorator


def human_readable_date(time: int) -> str:
    seconds = time // 1_000_000_000
    nanos = time % 1_000_000_000

    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()

    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{nanos:09d}%:z")


# def timed_run(op: Callable[..., StepLogModel], *args: object, **kwargs: object) -> StepLogModel:
def timed_run(op, *args: object, **kwargs: object):
    start_date: int = time.time_ns()
    start_time: int = time.perf_counter_ns()

    try:
        log = op(*args, **kwargs)
    finally:
        delta = time.perf_counter_ns() - start_time

    # NOTE: we could simplyfy this by having a marshalling method
    if isinstance(log, StepLogModel | PlaybookLog | ActLog):
        end_date: int = time.time_ns()
        log.timing.duration_sec = delta / 1_000_000_000.0
        log.timing.start_date = human_readable_date(start_date)
        log.timing.start_date_timestamp = start_date
        log.timing.end_date = human_readable_date(end_date)

    return log
