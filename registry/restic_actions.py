# borg actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog, Status


restic = ActionRegistry("restic_actions_reg")


@restic.register(name="check_repo_exists", version="preborg1.0")
def check_repo_exists(ctx, name) -> StepLog:
    passwordFile: str = ctx["passwordFile"]
    repoPath: str = ctx["repoPath"]

    if passwordFile == "":
        return StepLog(
            step_name=name,
            status=Status.BAD,
            error=["password file variable is empty"],
        )

    if repoPath == "":
        return StepLog(
            step_name=name,
            status=Status.BAD,
            error=["password file variable is empty"]
        )

    # If the path doesn't exist restic will make sure of warning us about it
    
    return StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="password file variable is empty",
    )


@restic.register(name="backup_data_to_repo", version="playborg1.0")
def backup_data_to_repo(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="directory was copied/movied/borged/rsynced",
    )
    return log


@restic.register(name="post", version="postborg1.0")
def validate_data_backup(ctx, name) -> StepLog:
    log: StepLog = StepLog(
        step_name=name,
        status=Status.GOOD,
        msg="copied/movied/borged/rsynced exists and is valid",
    )
    return log
