from playbook.action_registry import ActionRegistry
from playbook.models import StepLog

import sys
import json
import docker
import subprocess
from typing import List, Dict, Any, Tuple


dockeractions = ActionRegistry("docker_actions_reg")


@dockeractions.register(name="get_service_container", version="")
def get_service_container(ctx, name) -> StepLog:
    client = docker.from_env()

    filters: Dict[str, Any]= {"label": [f"com.docker.compose.service=gitea-db"]}
    print(client.containers.list(filters=filters, all=True), file=sys.stderr)

    return StepLog.ok(name, "cool beans")
