# restic actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog
from playbook import ContextWrapper

from registry.docker_actions import dockeractions

import sys
import json
import docker
import subprocess
from typing import List, Dict, Any, Tuple


dbpgactions = ActionRegistry("dbpg_actions_reg")
 
 
@dbpgactions.register(name="dump_pg_database", version="")
def dump_pg_database(ctx, name) -> StepLog:
    c = ContextWrapper(ctx)
    return StepLog.ok(name, "")
