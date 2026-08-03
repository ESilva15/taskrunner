# restic actions registry
from playbook.action_registry import ActionRegistry
from playbook.logging_models import StepLogModel
from playbook.models import ContextChecker

from registry.docker_actions import dockeractions

import sys
import json
import docker
import subprocess


dbpgactions = ActionRegistry(name="dbpg_actions_reg")
 
 
@dbpgactions.register(name="dump_pg_database", version="")
@ContextChecker.requires("database", "compose")
def dump_pg_database_from_container(ctx, name) -> StepLogModel:
    print(ctx, file=sys.stderr)
    return StepLogModel.ok(name, "", pipe_ctx={"new_data": "coolData"})
