# In this file we will only put premade steps

from playbook.models import StepLog, Status
from playbook.action_registry import ActionRegistry


# Module wide registry with built in functions
registry: ActionRegistry = ActionRegistry("testrunner_registry")
