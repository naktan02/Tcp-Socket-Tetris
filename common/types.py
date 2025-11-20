from dataclasses import dataclass
from enum import Enum


@dataclass
class PlayerInfo:
    id: int
    name: str


class GameType(str, Enum):
    TETRIS = "TETRIS"
    PUYO = "PUYO"  # 미래용


class ActionCode(str, Enum):
    NONE = "NONE"
    LEFT = "L"
    RIGHT = "R"
    ROTATE = "RT"
    SOFT_DROP = "SD"
    HARD_DROP = "HD"
