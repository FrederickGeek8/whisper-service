from typing import Literal, Optional

ErrorReason = Literal["format"]


class CacheIncoherentError(ValueError):
    def __init__(self, *args: object, reason: Optional[ErrorReason] = None) -> None:
        super().__init__(*args)
        self.reason = reason


def confirm(message: str):
    return input(f"{message} (y/N) ").strip().lower() == "y"
