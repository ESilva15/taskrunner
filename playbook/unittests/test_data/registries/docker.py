from os import error

from yaml import dump

from playbook import models
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog, ContextChecker

import sys
import json
import docker
import subprocess
from typing import List, Dict, Any, Tuple
# from docker.models.containers import Container


dockeractions = ActionRegistry("docker_actions_reg")


@dockeractions.register(name="get_service_container_name", version="")
@ContextChecker.requires("service_name")
def get_service_container_name(ctx, name) -> StepLog:
    client = docker.from_env()

    filters: Dict[str, Any]= {
        "label": [f"com.docker.compose.service={ctx["service_name"]}"]
    }
    containers = client.containers.list(filters=filters, all=True)

    if not containers:
        return StepLog.fail(name, [{
            "status": "failed", 
            "output": f"no container found for service {ctx["service_name"]}"}
        ])

    new_data = {"container": containers[0].id}
    return StepLog.ok(name, f"found container {containers[0].id}", pipe_ctx=new_data)


@dockeractions.register(name="dump_container_pg_db", version="")
@ContextChecker.requires("container", "dump_path", "db_user", "database")
def dump_container_pg_db(ctx, name) -> StepLog:
    client = docker.from_env()
    container = client.containers.get(ctx["container"])

    res = container.exec_run(
        cmd=f"pg_dump -U {ctx["db_user"]} {ctx["database"]}",
        stream=False,  # change to True to stream directly to host file (need to check)
        demux=True,
    )
    stdout, stderr = res.output

    if stderr:
        if not isinstance(stderr, bytes):
            return StepLog.fail(name, [{"status": "failed", "output": "stderr is not bytes"}])
        if res.exit_code != 0:
            error_msg = stderr.decode("utf-8") if stderr else "dump failed with no output"
            return StepLog.fail(name, [{"status": "failed", "output": error_msg}])

    if not isinstance(stdout, bytes):
        return StepLog.fail(name, [{"status": "failed", "output": "stdout is not bytes"}])
    with open(ctx["dump_path"], "wb") as f:
        f.write(stdout)

    return StepLog.ok(name, "database dump successful")    
