# restic actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog
from playbook.models import ContextChecker

from registry.docker_actions import dockeractions

import sys
import json
import docker
import subprocess
from typing import List, Dict, Any, Tuple


dbpgactions = ActionRegistry("dbpg_actions_reg")
 
 
@dbpgactions.register(name="dump_pg_database", version="")
@ContextChecker.requires("database")
def dump_pg_database(ctx, name) -> StepLog:
    print(ctx, file=sys.stderr)
    return StepLog.ok(name, "", pipe_ctx={"new_data": "coolData"})
