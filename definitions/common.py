from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    id: str
    display_name: str
