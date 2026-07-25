# borg actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog, Status

borgact = ActionRegistry("borg_actions_reg")

@borgact.register(name="pre", version="preborg1.0")
def pre(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="source directory exists",
    )
    return log


@borgact.register(name="play", version="playborg1.0")
def play(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="directory was copied/movied/borged/rsynced",
    )
    return log


@borgact.register(name="post", version="postborg1.0")
def post(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="copied/movied/borged/rsynced exists and is valid",
    )
    return log
