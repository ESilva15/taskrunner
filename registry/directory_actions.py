# directory actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog, Status

diract = ActionRegistry("directory_actions_reg")

@diract.register(name="directory_exists", version="stat1.0")
def directory_exists(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="source directory exists",
    )
    return log


@diract.register(name="copy_directory", version="cp1.0")
def copy_directory(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="directory was copied/movied/borged/rsynced",
    )
    return log


@diract.register(name="verify_copy", version="verify1.0")
def verify_copy(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="copied/movied/borged/rsynced exists and is valid",
    )
    return log
