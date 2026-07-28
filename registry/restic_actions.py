# restic actions registry
from playbook.action_registry import ActionRegistry
from playbook.models import StepLog

import sys
import json
import subprocess
from typing import List, Dict, Any, Tuple


# NOTE:
# most restic run commands seem to be the same pattern of:
# restic command -> parse output -> grab errors
# we can create a class for this I reckon


restic = ActionRegistry("restic_actions_reg")


def parse_output(line: str) -> List[Dict[str, Any]]:
    errors = []
    for line in line.split('\n'):
        if line.startswith("{"):  # } treesitter is borked lmao
            data = json.loads(line)
            errors.append(data)
    return errors


def find_restic_errors(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    errors = []
    for s in data:
        if s["message_type"] == "exit_error":
            errors.append(s)
    return errors


def run_restic_command(cmd: List[str]) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Executes a restic command, streams output live to terminal, 
    and returns (returncode, parsed_json_objects).
    """
    parsed_json = []
    
    # Start process with combined stdout/stderr pipe
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # NOTE: is this what we want?
    assert process.stdout is not None

    # Read line-by-line in real-time
    for line in iter(process.stdout.readline, ''):
        # Write live output directly to terminal screen
        sys.stdout.write(line)
        sys.stdout.flush()

        # Parse and capture valid JSON objects on the fly
        clean_line = line.strip()
        if clean_line.startswith('{'): # }
            try:
                data = json.loads(clean_line)
                parsed_json.append(data)
            except json.JSONDecodeError:
                pass

    process.stdout.close()
    returncode = process.wait()
    return returncode, parsed_json


@restic.register(name="check_restic_environment", version="")
def check_restic_environment(ctx, name: str = "") -> StepLog:
    for v in ["passwordFile", "repoPath", "sourcePath", "serviceTag"]:
        if not ctx.get(v):
            return StepLog.fail(name, [f"{v} variable is empty"])

    return StepLog.ok(name, "environment configuration seems to be valid")


@restic.register(name="create_restic_repo", version="")
def create_restic_repo(ctx, name: str = "") -> StepLog:
    cmd = ["restic", "init", "--json", "-r", ctx["repoPath"], 
         "--password-file", ctx["passwordFile"]]

    returncode, json_output = run_restic_command(cmd)

    errors: List[Dict[str, Any]] = find_restic_errors(json_output)

    # Handle error messages in JSON output
    if len(errors) > 0:
        return StepLog.fail(name, errors)

    # Make sure the return code is good too
    if returncode != 0:
        return StepLog.fail(name, [{"status": "failed", "output": json_output}])

    return StepLog.ok(name, "repo create succesfully")


@restic.register(name="create_repo_if_not_exists", version="")
def create_repo_if_not_exists(ctx, name: str = "") -> StepLog:
    log: StepLog = check_if_repo_exists(ctx, "")

    msg: str = ""
    if log.failed:
        # Repo doesn't exist is error code 10
        if log.error[0]["code"] != 10:
            return StepLog.fail(name, [{"status": "failed", "output": log.error}])

        # Create repo
        repoCreateLog: StepLog = create_restic_repo(ctx, name + f".{create_restic_repo}")
        if repoCreateLog.failed:
            return StepLog.fail(name, [{"status": "failed", "output": repoCreateLog.error}])
        msg = "repo created"
    else:
        msg = "repo already exists"


    return StepLog.ok(name, msg)


@restic.register(name="check_if_repo_exists", version="")
def check_if_repo_exists(ctx, name: str = "") -> StepLog:
    cmd = ["restic", "-r", ctx["repoPath"], "cat", "config", "--json",
           "--password-file", ctx["passwordFile"]]
    returncode, json_output = run_restic_command(cmd)

    errors: List[Dict[str, Any]] = find_restic_errors(json_output)

    # Handle error messages in JSON output
    if len(errors) > 0:
        return StepLog.fail(name, errors)

    # Make sure the return code is good too
    if returncode != 0:
        return StepLog.fail(name, [{"status": "failed", "output": json_output}])

    return StepLog.ok(name, "repo seems to exist")


@restic.register(name="backup_data_to_restic_repo", version="")
def backup_data_to_restic_repo(ctx, name) -> StepLog:
    out = subprocess.run(
        ["restic", "backup", ctx["sourcePath"], "--json", "--quiet",
         "-r", ctx["repoPath"], "--password-file", ctx["passwordFile"]],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    json_output: List[Dict[str, Any]] = parse_output(out.stdout)
    errors: List[Dict[str, Any]] = find_restic_errors(json_output)

    # Handle error messages in JSON output
    if len(errors) > 0:
        return StepLog.fail(name, errors)

    # Make sure the return code is good too
    if out.returncode != 0:
        return StepLog.fail(name, [{"status": "failed", "output": out.stdout}])

    # Return code is 0, so it was successful, output the message
    try:
        data = json.loads(out.stdout)
        msg = data
    except:
        msg = {
            "status": "ran succesfully, but an error occurred parsing the output",
            "output": out.stdout,
        }

    return StepLog.ok(name, str(msg))


#-- BIG NOTE ------------------------------------------------------------------#
# I will use the restic registry for database actions until I make it so cross #
# registry calls with context are possible. But right now the yaml config      #
# doesnt support that anyway.                                                  #
#------------------------------------------------------------------------------#
