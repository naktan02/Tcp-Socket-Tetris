from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class Action(Enum):
    LEFT = auto()
    RIGHT = auto()
    ROTATE = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    NONE = auto()


@dataclass
class GameState:
    board: List[List[int]]  # 0 = empty, >0 = color index
    score: int
    lines_cleared: int
    game_over: bool


class IGame:
    def step(self, action: Action) -> GameState:
        """한 틱 동안 action을 적용하고 새로운 상태를 반환."""
        raise NotImplementedError

    def get_state(self) -> GameState:
        raise NotImplementedError
