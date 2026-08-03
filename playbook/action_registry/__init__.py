import os
import sys
import importlib.util
from playbook.logging_models import StepLogModel
from typing import Callable
from pydantic import BaseModel, PrivateAttr


ActionFn = Callable[[dict[str, object], str], StepLogModel]


class Action(BaseModel):
    name: str
    fn: ActionFn
    ver: str


class ActionRegistry(BaseModel):
    name: str
    _actions: dict[str, Action] = PrivateAttr(default_factory=dict)

    def register(self, name: str, version: str):
        """Decorator to register python functions with a name and version."""
        def decorator(function: ActionFn):
            self._actions[name] = Action(name=name, fn=function, ver=version)
            return function
        return decorator

    def get(self, name: str, ver: str = '*') -> ActionFn:
        if name not in self._actions:
            raise ValueError(
                f"Action '{name}' is not registered in registry '{self.name}'")

        return self._actions[name].fn

    @staticmethod
    def load_registries_from_file(file_path: str) -> list[ActionRegistry]:
        abs_path = os.path.abspath(file_path)
        module_name = os.path.splitext(os.path.basename(abs_path))[0]

        spec = importlib.util.spec_from_file_location(module_name, abs_path)
        if spec is None or spec.loader is None:
            raise ImportError(
                f"could not create spec for registry file: {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        discovered_registries = [
            obj for obj in vars(module).values()
            if isinstance(obj, ActionRegistry)
        ]

        if not discovered_registries:
            raise ValueError(f"No ActionRegistry instances were found in '{file_path}'")

        return discovered_registries
