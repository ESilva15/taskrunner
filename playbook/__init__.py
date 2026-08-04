from __future__ import annotations
from re import A

import yaml
from abc import ABC, abstractmethod
from pydantic import BaseModel

from playbook.models import ActModel, PlaybookModel, StepModel, timed_run
from playbook.logging_models import PlaybookLog, Status, StepLogModel
from playbook.action_registry import ActionFn, ActionRegistry


class StepIF(ABC):
    @abstractmethod
    def run(self, ctx: dict[str, object]) -> StepLogModel:
        """Perform the actions."""
        pass

    @abstractmethod
    def get_action_names(self) -> list[str]:
        """ Return a mapping of action roles (pre, play, post) to function names. """
        pass

#     def log_file_name(self, start_date_ns: int) -> str:
#         """ Format to ISO 8601. """
#         seconds = start_date_ns // 1_000_000_000
#         ms = (start_date_ns % 1_000_000_000) // 1_000_000
#
#         dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
#
#         return dt.strftime(f"{self.name}_%Y-%m-%d_%H-%M-%S.{ms:03d}.log")
#
#     def _write_log(self, log: StepLogModel):
#         try:
#             with open(log.log_file_path, "w") as file:
#                 json.dump(asdict(log), file)
#         except Exception as e:
#             raise PlaybookError(f"failed to create log file {e}") from e
#         return ""
#
#     def _play_act(self) -> StepLogModel:
#         playLog: StepLogModel = StepLogModel(
#             step_name=self.name,
#             status=Status.GOOD,
#             duration_sec=0,
#             msg="",
#             error=[],
#             substeps=[],
#         )
#
#         for a in self._acts:
#             log: StepLogModel = self._play_steps(self._acts[a])
#
#             if log.failed:
#                 playLog.error.append({
#                     "status": "failed",
#                     "output": f"failed in step: {log.step_name}"
#                 })
#                 playLog.status = Status.BAD
#                 break
#
#         if playLog.status == Status.GOOD:
#             playLog.msg = "success"
#
#         return playLog


class PlaybookYAMLParser():
    @staticmethod
    def _parse_registries(reg_names: list[str]) -> list[ActionRegistry]:
        registries: list[ActionRegistry] = []
        for reg in reg_names:
            registries.extend(ActionRegistry.load_registries_from_file(reg))
        return registries

    @staticmethod
    def _parse_steps(steps: list[dict[str, object]],
                     registries: list[ActionRegistry]) -> list[StepModel]:
        step_list: list[StepModel] = []
        for step in steps:
            if not isinstance(step['name'], str):
                raise ValueError(
                    f"name must of type `str` not `{type(step["name"])}`")
            if not isinstance(step['action'], str):
                raise ValueError(
                    f"action must of type `str` not `{type(step["action"])}`")
            if not isinstance(step['context'], dict):
                raise ValueError(
                    f"context must of type `dict` not `{type(step["context"])}`")

            name: str = step['name']
            action: str = step['action']
            context: dict[str, object] = step['context']

            found = False
            fn: ActionFn
            for reg in registries:
                try:
                    fn = reg.get(action)
                    found = True
                except:
                    continue

            if not found:
                raise ValueError(
                    f"Unable to find function `{action}` in any registry")

            step_list.append(StepModel(name=name, action=fn, context=context))

        return step_list

    @staticmethod
    def _parse_acts(acts_data: list[dict[str, object]],
                    registries: list[ActionRegistry]) -> list[ActModel]:
        acts: list[ActModel] = []
        for act in acts_data:
            if not isinstance(act["name"], str):
                raise ValueError(
                    f"name must of type `str` not `{type(act["name"])}`")

            if not isinstance(act["steps"], list):
                raise ValueError(
                    f"steps must of type `list` not `{type(act["steps"])}`")

            name: str = act["name"]
            steps: list[dict[str, object]] = act["steps"]

            step_list = PlaybookYAMLParser._parse_steps(steps, registries)
            modeled_act: ActModel = ActModel(name=name, steps=step_list)
            acts.append(modeled_act)

        return acts

    @staticmethod
    def from_yaml(fp: str) -> Playbook:
        with open(fp, "rb") as source_file:
            data = yaml.safe_load(source_file)

        reg_yaml = data.get("registries", [])
        registries = PlaybookYAMLParser._parse_registries(reg_yaml)

        acts_yaml = data.get("acts", {})
        acts: list[ActModel] = PlaybookYAMLParser._parse_acts(
            acts_yaml, registries)

        global_context = data.get("global_context", {})

        log_dir: str = data.get("log_dir", "./")
        playbook_name: str = data.get("playbook_name")

        new_playbook: PlaybookModel = PlaybookModel(
            playbook_name=playbook_name,
            acts=acts,
            log_dir=log_dir,
            registries=registries,
            global_context=global_context
        )

        return Playbook(new_playbook)


class Playbook():
    model: PlaybookModel

    def __init__(self, model: PlaybookModel):
        self.model = model

    @property
    def acts(self) -> list[ActModel]:
        return self.model.acts

    @classmethod
    def from_yaml(cls, fp: str) -> Playbook:
        return PlaybookYAMLParser.from_yaml(fp)

    def view_playbook(self) -> str:
        return self.model.model_dump_json()

    def run_play(self) -> PlaybookLog:
        log: PlaybookLog = self.model.run()

        # if self.model.log_dir != "":
        #     log.log_file_path = os.path.join(
        #         self.model.log_dir, self.log_file_name(log.start_date_timestamp)
        #     )
        #     self._write_log(log)

        return log
