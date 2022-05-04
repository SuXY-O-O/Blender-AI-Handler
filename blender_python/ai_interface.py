class AiInterface:
    def __init__(self):
        raise TypeError("Should not use base AiInterface")

    def get_next(self, control_arg: list):
        return []

    def end(self) -> bool:
        return False
