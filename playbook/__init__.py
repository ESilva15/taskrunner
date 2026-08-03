from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from pydantic import BaseModel

from playbook.models import ActModel, PlaybookModel, timed_run
from playbook.logging_models import Status, StepLogModel
from playbook.action_registry import ActionFn



class StepIF(ABC):
    @abstractmethod
    def run(self, ctx: dict[str, object]) -> StepLogModel:
        """Perform the actions."""
        pass

    @abstractmethod
    def get_action_names(self) -> list[str]:
        """ Return a mapping of action roles (pre, play, post) to function names. """
        pass


# class PlaybookError(Exception):
#     """ Base exception for Playbook parsing and execution failures. """
#     pass


# @dataclass
# class StepEntry(object):
#     name: str
#     step: StepIF


# class Play(object):
#     def __init__(self, name: str, registries: dict[str, ActionRegistry]):
#         self.name: str = name
#         self.log_dir: str = ""
#         self._context: dict[str, object] = {}
#         self._acts: dict[str, list[CustomStep]] = {}
#         self._steps: list[StepEntry] = []
#         self._registries: dict[str, ActionRegistry] = {
#             registry.name: registry} | registries
#
#
#     def add_step(self, name: str, stepRunner: StepIF):
#         self._steps.append(StepEntry(name=name, step=stepRunner))
#
#     def view_playbook(self) -> str:
#         acts_info = {}
#         for act_name, step_list in self._acts.items():
#             steps_info = []
#             for s in step_list:
#                 steps_info.append({
#                     "name": s.name,
#                     "actions": s.get_action_names()
#                 })
#
#             new_act = {
#                 "name": act_name,
#                 "steps": steps_info
#             }
#
#             acts_info[act_name] = new_act
#
#         registry_data = []
#         for reg in self._registries.values():
#             registry_data.append(reg.manifest())
#
#         data = {
#             "name": self.name,
#             "registries": registry_data,
#             "number_of_acts": len(acts_info),
#             "acts": acts_info,
#         }
#
#         return json.dumps(data)
#
#     def play(self) -> StepLogModel:
#         log: StepLogModel = timed_run(self._play_act)
#
#         if self.log_dir != "":
#             log.log_file_path = os.path.join(
#                 self.log_dir, self.log_file_name(log.start_date_timestamp)
#             )
#             self._write_log(log)
#
#         return log
#
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
#
#     def _play_steps(self, steps: list[CustomStep]) -> StepLogModel:
#         playLog: StepLogModel = StepLogModel(
#             step_name=self.name,
#             status=Status.GOOD,
#             duration_sec=0,
#             msg="",
#             error=[],
#             substeps=[],
#         )
#
#         prev_ctx: dict[str, object] = {}
#         for step in steps:
#             log: StepLogModel = timed_run(step.run, self._context | prev_ctx)
#             prev_ctx = log.pipe_ctx
#
#             playLog.substeps.append(log)
#
#             if log.failed:
#                 playLog.error.append({
#                     "status": "failed",
#                     "output": f"failed in step: {step.name}"
#                 })
#                 playLog.status = Status.BAD
#                 break
#
#         if playLog.status == Status.GOOD:
#             playLog.msg = "success"
#
#         return playLog
#
#     def _get_function_from_registry(self, fn_name) -> ActionFn:
#         for reg in self._registries.values():
#             try:
#                 return reg.get(fn_name, "*")
#             except ValueError:
#                 continue
#
#         raise ValueError(f"no function with name '{fn_name}' was found")
#
#     def _build_custom_step(self, name, actions, ctx) -> CustomStep:
#         functionlist: list[ActionFn] = []
#         for f in actions:
#             try:
#                 fn = self._get_function_from_registry(actions[f])
#                 functionlist.append(fn)
#             except KeyError as e:
#                 raise PlaybookError(
#                     f"Step '{name}' is missing required action field: {e}") from e
#
#         return CustomStep(name, functionlist, ctx)


class Playbook():
    model: PlaybookModel

    def __init__(self, model: PlaybookModel):
       self.model = model

    @property
    def acts(self) -> list[ActModel]:
        return self.model.acts
    
    @classmethod
    def from_yaml(cls, fp: str) -> Playbook:
        try:
            new_playboook = PlaybookModel.from_yaml_file(fp)
            return Playbook(new_playboook)
        except Exception as e:
            raise e

    def view_playbook(self) -> str:
        return self.model.model_dump_json()

    def run_play(self):
        return self.model.run()
