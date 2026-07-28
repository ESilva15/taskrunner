from dataclasses import dataclass
from playbook.models import StepLog, ActionFn
from typing import Callable, Dict, Any


@dataclass
class Action(object):
    name: str
    fn: ActionFn
    ver: str


class ActionRegistry:
    def __init__(self, name: str):
        self.name: str = name
        self.__actions = {}

    def register(self, name: str, version: str):
        """Decorator to register python functions with a name and version."""
        def decorator(function: ActionFn):
            if name not in self.__actions:
                self.__actions[name] = {}

            self.__actions[name][version] = function
            return function

        return decorator
    
    def get(self, name: str, ver: str) -> ActionFn:
        if name not in self.__actions:
            raise ValueError(f"Action '{name}' is not registered in registry '{self.name}'")
        
        versions_dict = self.__actions[name]
        if not versions_dict:
            raise ValueError(f"No registered versions found for function '{name}'")

        if ver == "*":
            return next(iter(versions_dict.values()))

        if ver not in self.__actions[name]:
            raise ValueError(f"Version '{ver}' is not registered for function '{name}'")

        return versions_dict[ver]

    def manifest(self):
        functions = {}
        for fn_name, versions_dict in self.__actions.items():
            functions[fn_name] = list(versions_dict.keys())
        return {"registry_name": self.name, "functions": functions}
