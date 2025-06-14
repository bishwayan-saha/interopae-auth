from typing import Any


class InteropAEException(Exception):

    def __init__(self, message: Any, status_code: int) -> None:
        self.message = message
        self.status_code = status_code