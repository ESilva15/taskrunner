from __future__ import annotations

import os
import sys
import yaml
import json
import time
import datetime
import importlib.util
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from playbook.models import Status, StepLog
from playbook.action_registry import ActionFn, ActionRegistry
from playbook.premade_steps_registry import registry


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

    @abstractmethod
    def get_action_names(self) -> Dict[str, str]:
        """ Return a mapping of action roles (pre, play, post) to function names. """
        pass

    def __timed_run(self, op) -> StepLog:
        """Function that sets the duration_sec field on the log."""
        start_time: int = time.perf_counter_ns()
        log: StepLog = op()
        log.duration_sec = time.perf_counter_ns() - start_time

        return log

    def run(self, name: str) -> StepLog:
        """ Run the step. """
        start_time: int = time.perf_counter_ns()

        substeps: List[StepLog] = []
        status: Status = Status.GOOD
        for op in [self.pre, self.play, self.post]:
            log: StepLog = self.__timed_run(op)
            status = Status.BAD if log.failed else Status.GOOD

            substeps.append(log)

            if status == Status.BAD:
                break

        delta: int = time.perf_counter_ns() - start_time
         
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
    """ Setup custom steps. """

    def __init__(
        self, 
        name: str,
        pre_fn: ActionFn,
        play_fn: ActionFn,
        post_fn: ActionFn,
        context: Dict[str, Any]
    ):
        self.name: str = name

        self.pre_fn = pre_fn
        self.play_fn = play_fn
        self.post_fn = post_fn

        self.__context = context

    def pre(self) -> StepLog:
        return self.pre_fn(self.__context, self.name)
    
    def play(self) -> StepLog:
        return self.play_fn(self.__context, self.name)

    def post(self) -> StepLog:
        return self.post_fn(self.__context, self.name)

    def get_action_names(self) -> Dict[str, str]:
        return {
            "pre": self.pre_fn.__name__,
            "play": self.pre_fn.__name__,
            "post": self.pre_fn.__name__,
        }


class PlaybookError(Exception):
    """ Base exception for Playbook parsing and execution failures. """
    pass


@dataclass
class StepEntry(object):
    name: str
    step: StepIF


class Play(object):
    def __init__(self, name : str, registries: Optional[List[ActionRegistry]] = None):
        self.name: str = name
        self.__steps: List[StepEntry] = []
        self.__registries: List[ActionRegistry] = [registry] + (registries or [])

    @staticmethod
    def __load_registry_file(file_path: str) -> List[ActionRegistry]:
        abs_path = os.path.abspath(file_path)
        module_name = os.path.splitext(os.path.basename(abs_path))[0]
    
        spec = importlib.util.spec_from_file_location(module_name, abs_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not create spec for registry file: {file_path}")
    
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    
        discovered_registries = [
            obj for obj in vars(module).values()
            if isinstance(obj, ActionRegistry)
        ]

        if not discovered_registries:
            raise PlaybookError(f"No ActionRegistry instances were found in '{file_path}'")
    
        return discovered_registries

    def add_step(self, name: str, stepRunner : StepIF):
        self.__steps.append(StepEntry(name=name, step=stepRunner))

    def view_playbook(self) -> str:
        steps_info = []
        for s in self.__steps:
            steps_info.append({
                "name": s.name,
                "actions": s.step.get_action_names()
            })

        registry_data = []
        for reg in self.__registries:
            registry_data.append(reg.manifest())

        data = {
            "name": self.name,
            "registries": registry_data,
            "number_of_steps": len(steps_info),
            "steps": steps_info,
        }

        return json.dumps(data)

    def play(self) -> StepLog:
        start_time: int = time.perf_counter_ns()
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

        delta: int = time.perf_counter_ns() - start_time
        playLog.duration_sec = delta

        if playLog.status == Status.GOOD:
            playLog.msg = "success"

        return playLog

    def __get_function_from_registry(self, fn_name) -> ActionFn:
        for reg in self.__registries:
            try:
                return reg.get(fn_name, "*")
            except ValueError:
                continue

        raise ValueError(f"no function with name '{fn_name}' was found")

    def __build_custom_step(self, name, actions, ctx) -> CustomStep:
        try:
            pre_fn = self.__get_function_from_registry(actions["pre"])
            play_fn = self.__get_function_from_registry(actions["play"])
            post_fn = self.__get_function_from_registry(actions["post"])
        except KeyError as e:
            raise PlaybookError(f"Step '{name}' is missing required action field: {e}") from e

        return CustomStep(name=name, pre_fn=pre_fn, play_fn=play_fn, post_fn=post_fn, context=ctx)

    @classmethod
    def from_yaml(cls, fp: str, registries: Optional[List[ActionRegistry]] = None) -> Play:
        """ Loads the playbook from a given YAML file. """
        try:
            with open(fp, "r") as f:
                file_contents = f.read()
        except FileNotFoundError as e:
           raise PlaybookError(f"Playbook file not found: {fp}") from e
        except Exception as e:
            raise PlaybookError(f"Failed to read file {fp}: {e}") from e 
        
        yaml_dir = os.path.dirname(os.path.abspath(fp))
        return cls.__from_yaml_str(file_contents, base_dir=yaml_dir)

    @classmethod
    def __from_yaml_str(cls, yaml_str: str, base_dir: str = ".") -> Play:
        data = None
        try:
            data = yaml.safe_load(yaml_str)
        except Exception as e:
            raise PlaybookError(f"YAML Syntax error: {e}") from e

        if not isinstance(data, dict) or "playbook_name" not in data:
            raise PlaybookError("YAML must contain a top-level 'playbook_name' field.")

        # LOAD THE CUSTOM REGISTRIES
        custom_registries: List[ActionRegistry] = []
        registry_paths = data.get("registries", [])

        for reg_path in registry_paths:
            full_path = os.path.join(base_dir, reg_path) if not os.path.isabs(reg_path) else reg_path
            try:
                regs = cls.__load_registry_file(full_path)
                custom_registries.extend(regs)
            except Exception as e:
                raise PlaybookError(f"Error loading registry '{reg_path}': {e}") from e

        playbook = cls(data["playbook_name"], registries=custom_registries)

        for idx, step_cfg in enumerate(data.get("steps", [])):
            step_name = step_cfg.get("name", f"step_{idx}")
            actions = step_cfg.get("actions", {})
            context = step_cfg.get("context", {})

            if not isinstance(actions, dict) or len(actions) != 3:
                raise PlaybookError(
                    f"Step '{step_name}' (index {idx}) must define an 'actions' map "
                    "containing 'pre', 'play' and 'post'"
                )
            
            try:
                customStep: CustomStep = playbook.__build_custom_step(step_name, actions, context)
                playbook.add_step(step_cfg["name"], customStep)
            except Exception as e:
                raise PlaybookError(f"Error configuring step '{step_name}': {e}") from e

        return playbook
