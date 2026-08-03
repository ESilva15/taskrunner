# directory actions registry
from playbook.action_registry import ActionRegistry
from playbook.logging_models import StepLogModel

import os


diract = ActionRegistry(name="directory_actions_reg")


@diract.register(name="directory_exists", version="stat1.0")
def directory_exists(ctx, name) -> StepLogModel:
    if not os.path.exists(ctx["repoPath"]):
        return StepLogModel.fail(name, [
            {"status": "failed", "output": f"dir '{ctx["repoPath"]}' doesn't exist"}]
        )
    return StepLogModel.ok(name, "directory exists")


@diract.register(name="create_dir", version="stat1.0")
def create_dir(ctx, name) -> StepLogModel:
    try:
        os.makedirs(ctx["repoPath"])
    except Exception as e:
        return StepLogModel.fail(name, [{"status": "failed", "output": str(e)}])

    return StepLogModel.ok(name, "dir create successfully")


@diract.register(name="create_dir_if_not_exists", version="stat1.0")
def create_dir_if_not_exists(ctx, name) -> StepLogModel:
    log: StepLogModel = directory_exists(ctx, name + f".{directory_exists.__name__}")
    msg: str = ""
    if log.failed:
        dir_creation_log: StepLogModel = create_dir(ctx, name + f".{create_dir.__name__}")
        if dir_creation_log.failed:
            return StepLogModel.fail(name, [{"status": "failed", "output": dir_creation_log}])
        msg = "dir created succesfully" 
    else:
        msg = "dir already exists" 

    return StepLogModel.ok(name, msg)
