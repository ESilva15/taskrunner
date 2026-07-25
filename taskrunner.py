import json
from playbook import StepLog, CustomStep, Play, Status
from dataclasses import asdict

def pre(ctx) -> StepLog:
    ctx["a"] = 5

    return StepLog(
        "pre something",
        Status.GOOD, 
        0,
        msg="set 5",
    )

def play(ctx):
    ctx["a"] = ctx["a"] + 10

    return StepLog(
        "play something",
        Status.BAD, 
        0,
        msg="added 10",
    )

def post(ctx):
    ctx["a"] = ctx["a"] / 2

    return StepLog(
        "post something",
        Status.GOOD, 
        0,
        msg=f"halved {ctx["a"]}",
    )
    

def main():
    newPlay: Play
    try:
        newPlay = Play.from_yaml("./playbook.yaml")
    except Exception as e:
        print(f"Failed to load playbook: {e}")
        exit(1)

    print(newPlay.view_playbook())

    # print(json.dumps(asdict(newPlay.play()), indent=2))


if __name__ == "__main__":
    main()
