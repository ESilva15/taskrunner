import json
import argparse
import traceback
from typing import List
from playbook import Play
from dataclasses import asdict

from playbook.action_registry import ActionRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Playbook Taskrunner")

    # Flag for the playbook file
    parser.add_argument(
        "-p", "--playbook",
        type=str,
        required=True,
        help="Path to the playbook yaml file"
    )

    return parser.parse_args()


def main():
    args: argparse.Namespace = parse_args()

    newPlay: Play
    try:
        newPlay = Play.from_yaml(args.playbook)
    except Exception as e:
        print(f"Failed to load playbook: {e}")
        traceback.print_exc()
        exit(1)

    print(newPlay.view_playbook())
    # print(json.dumps(asdict(newPlay.play()), indent=2))


if __name__ == "__main__":
    main()
