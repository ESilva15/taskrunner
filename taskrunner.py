import argparse
import traceback

from playbook import Playbook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Playbook Taskrunner")

    # Flag for the playbook file
    _ = parser.add_argument(
        "-p", "--playbook",
        type=str,
        required=True,
        help="Path to the playbook yaml file"
    )

    return parser.parse_args()


def main():
    args: argparse.Namespace = parse_args()

    newPlay: Playbook
    try:
        newPlay = Playbook.from_yaml(args.playbook)
    except Exception as e:
        print(f"Failed to load playbook: {e}")
        traceback.print_exc()
        exit(1)

    # print(newPlay.view_playbook())
    log = newPlay.run_play()
    print(log.model_dump_json())
    # print(json.dumps(asdict(newPlay.run_play()), indent=2))


if __name__ == "__main__":
    main()
