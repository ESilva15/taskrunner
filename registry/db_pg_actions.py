# restic actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog

import sys
import json
import docker
import subprocess
from typing import List, Dict, Any, Tuple


dbpgactions = ActionRegistry("dbpg_actions_reg")


@dbpgactions.register(name="dump_pg_database", version="")
def dump_pg_database(ctx, name) -> StepLog:
    return StepLog.ok(name, "")


# NOTE: this functions ought to be in their own registry, but I need inter
# registry communication to be possible first
###############################################################################
##### DOCKER FUNCTIONS ########################################################

@dbpgactions.register(name="get_service_container", version="")
def get_service_container(ctx, name) -> StepLog:
    client = docker.from_env()

    filters: Dict[str, Any]= {"label": [f"com.docker.compose.service=gitea-db"]}
    print(client.containers.list(filters=filters, all=True), file=sys.stderr)

    return StepLog.ok(name, "cool beans")
