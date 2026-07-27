# directory actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog

import os


diract = ActionRegistry("directory_actions_reg")


@diract.register(name="directory_exists", version="stat1.0")
def directory_exists(ctx, name) -> StepLog:
    if not os.path.exists(ctx["repoPath"]):
        return StepLog.fail(name, [
            {"status": "failed", "output": f"dir '{ctx["repoPath"]}' doesn't exist"}]
        )
    return StepLog.ok(name, "directory exists")


@diract.register(name="create_dir", version="stat1.0")
def create_dir(ctx, name) -> StepLog:
    try:
        os.makedirs(ctx["repoPath"])
    except Exception as e:
        return StepLog.fail(name, [{"status": "failed", "output": str(e)}])

    return StepLog.ok(name, "dir create successfully")


@diract.register(name="create_dir_if_not_exists", version="stat1.0")
def create_dir_if_not_exists(ctx, name) -> StepLog:
    log: StepLog = directory_exists(ctx, name + f".{directory_exists.__name__}")
    msg: str = ""
    if log.failed:
        dir_creation_log: StepLog = create_dir(ctx, name + f".{create_dir.__name__}")
        if dir_creation_log.failed:
            return StepLog.fail(name, [{"status": "failed", "output": dir_creation_log}])
        msg = "dir created succesfully" 
    else:
        msg = "dir already exists" 

    return StepLog.ok(name, msg)
