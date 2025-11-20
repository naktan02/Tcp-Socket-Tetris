from __future__ import annotations
from dataclasses import dataclass
from typing import List
import random

from .base import IGame, GameState, Action
from common.constants import BOARD_WIDTH, BOARD_HEIGHT

# 테트로미노 정의 (회전 상태 포함)
TETROMINOES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}
PIECES = list(TETROMINOES.keys())


def empty_board() -> List[List[int]]:
    return [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]


@dataclass
class FallingPiece:
    kind: str
    rotation: int
    x: int
    y: int
    color: int


class TetrisGame(IGame):
    def __init__(self, seed: int | None = None):
        self.board = empty_board()
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.rng = random.Random(seed)
        self.current: FallingPiece | None = None
        self.next_kind: str | None = None
        self.spawn_new_piece()

    def spawn_new_piece(self):
        if self.next_kind is None:
            kind = self.rng.choice(PIECES)
        else:
            kind = self.next_kind
        self.next_kind = self.rng.choice(PIECES)
        self.current = FallingPiece(
            kind=kind,
            rotation=0,
            x=BOARD_WIDTH // 2 - 2,
            y=0,
            color=PIECES.index(kind) + 1,
        )
        if self.check_collision(self.current.x, self.current.y, self.current.rotation):
            self.game_over = True

    def get_shape(self, kind: str, rotation: int):
        rotations = TETROMINOES[kind]
        return rotations[rotation % len(rotations)]

    def check_collision(self, nx: int, ny: int, nrot: int) -> bool:
        piece = self.current
        assert piece is not None
        shape = self.get_shape(piece.kind, nrot)
        for ox, oy in shape:
            x = nx + ox
            y = ny + oy
            if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
                return True
            if self.board[y][x] != 0:
                return True
        return False

    def lock_piece(self):
        piece = self.current
        if piece is None:
            return
        shape = self.get_shape(piece.kind, piece.rotation)
        for ox, oy in shape:
            x = piece.x + ox
            y = piece.y + oy
            if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                self.board[y][x] = piece.color
        self.clear_lines()
        self.spawn_new_piece()

    def clear_lines(self):
        new_board = []
        cleared = 0
        for row in self.board:
            if all(cell != 0 for cell in row):
                cleared += 1
            else:
                new_board.append(row)
        while len(new_board) < BOARD_HEIGHT:
            new_board.insert(0, [0] * BOARD_WIDTH)
        self.board = new_board
        if cleared:
            self.lines_cleared += cleared
            self.score += [0, 40, 100, 300, 1200][cleared]

    def soft_drop(self):
        if self.current is None:
            return
        if not self.check_collision(
            self.current.x, self.current.y + 1, self.current.rotation
        ):
            self.current.y += 1
        else:
            self.lock_piece()

    def hard_drop(self):
        if self.current is None:
            return
        while not self.check_collision(
            self.current.x, self.current.y + 1, self.current.rotation
        ):
            self.current.y += 1
        self.lock_piece()

    def move_horizontal(self, dx: int):
        if self.current is None:
            return
        nx = self.current.x + dx
        if not self.check_collision(nx, self.current.y, self.current.rotation):
            self.current.x = nx

    def rotate(self):
        if self.current is None:
            return
        nrot = self.current.rotation + 1
        if not self.check_collision(self.current.x, self.current.y, nrot):
            self.current.rotation = nrot

    def step(self, action: Action) -> GameState:
        if self.game_over:
            return self.get_state()

        if action == Action.LEFT:
            self.move_horizontal(-1)
        elif action == Action.RIGHT:
            self.move_horizontal(1)
        elif action == Action.ROTATE:
            self.rotate()
        elif action == Action.SOFT_DROP:
            self.soft_drop()
        elif action == Action.HARD_DROP:
            self.hard_drop()
        else:
            # NONE: 중력만
            self.soft_drop()

        return self.get_state()

    def get_state(self) -> GameState:
        temp = [row[:] for row in self.board]
        if self.current is not None and not self.game_over:
            shape = self.get_shape(self.current.kind, self.current.rotation)
            for ox, oy in shape:
                x = self.current.x + ox
                y = self.current.y + oy
                if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                    temp[y][x] = self.current.color
        return GameState(
            board=temp,
            score=self.score,
            lines_cleared=self.lines_cleared,
            game_over=self.game_over,
        )
