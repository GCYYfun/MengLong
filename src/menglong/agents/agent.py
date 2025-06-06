from ..ml_model import Model


class Agent:
    def __init__(
        self,
        model_id: str = None,
    ):
        # model
        if model_id is None:
            self.model = Model()
        else:
            self.model = Model(model_id=model_id)

    def run(self):
        pass
