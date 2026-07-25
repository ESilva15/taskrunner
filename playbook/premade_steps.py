from Service import StepIF, StepLog, Status


class DirectoryStep(StepIF):
    """ Pre made play to backup directories. """

    def __init__(self, source : str, destiny : str):
        self.name: str = f"backup {source} -> {destiny}"
        self.source: str = source
        self.destiny: str = destiny

    def pre(self) -> StepLog:
        return StepLog(
                step_name = "pre " + self.name,
                status = Status.GOOD,
                duration_sec=0,
                msg="",
                error= [],
                substeps=[]
                )
    
    def play(self) -> StepLog:
        return StepLog(
                step_name = "run " + self.name,
                status = Status.GOOD,
                duration_sec=0,
                msg="",
                error=[],
                substeps=[]
                )

    def post(self):
        return StepLog(
                step_name = "post " + self.name,
                status = Status.GOOD,
                duration_sec=0,
                msg="",
                error=[],
                substeps=[]
                )
