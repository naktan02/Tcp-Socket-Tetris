from __future__ import annotations
import threading
import time
from typing import Dict, List

from engine.tetris import TetrisGame
from engine.base import Action
from common.constants import TICK_INTERVAL
from common.protocol import OpCode, encode_line
from common.types import ActionCode


class GameSession:
    """
    - 서버가 TetrisGame 두 개를 돌리는 세션
    - run() 루프: 중력(gravity)만 처리
    - 입력 패킷이 오면 apply_input()에서 즉시 step() + 상태 브로드캐스트
    """

    def __init__(self, game_id: int, p1: "ClientSession", p2: "ClientSession"):
        self.id = game_id
        self.p1 = p1
        self.p2 = p2

        self.game_p1 = TetrisGame()
        self.game_p2 = TetrisGame()

        self.lock = threading.Lock()
        self.alive = True
        self.finished = False

        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    # ----------------------
    # 메인 틱 루프 (중력만)
    # ----------------------
    def _run(self):
        while self.alive:
            time.sleep(TICK_INTERVAL)
            with self.lock:
                if self.finished:
                    break

                # 중력만 적용
                s1 = self.game_p1.step(Action.NONE)
                s2 = self.game_p2.step(Action.NONE)

                self._broadcast_state(s1, s2)

                if s1.game_over or s2.game_over:
                    self._finish_game_locked(s1, s2)
                    break

    # ----------------------
    # 입력 즉시 처리
    # ----------------------
    def apply_input(self, player_id: int, code: ActionCode):
        """
        GameManager에서 호출.
        - 해당 플레이어의 게임에만 action 적용
        - 즉시 상태 브로드캐스트
        """
        with self.lock:
            if self.finished:
                return

            action = self._action_from_code(code)

            # 누가 누른 입력인지에 따라 해당 쪽만 step()
            if player_id == self.p1.player_id:
                s1 = self.game_p1.step(action)
                s2 = self.game_p2.get_state()
            elif player_id == self.p2.player_id:
                s2 = self.game_p2.step(action)
                s1 = self.game_p1.get_state()
            else:
                return  # 알 수 없는 플레이어

            self._broadcast_state(s1, s2)

            if s1.game_over or s2.game_over:
                self._finish_game_locked(s1, s2)

    # [NEW] 플레이어 중도 포기 처리
    def player_leave(self, player_id: int):
        with self.lock:
            if self.finished:
                return
            
            self.finished = True
            self.alive = False

            # 나간 사람이 패배 (LOSE), 남은 사람이 승리 (WIN)
            if player_id == self.p1.player_id:
                # P1이 나감 -> P2 승리
                self.p1.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))
                self.p2.send_packet(encode_line(OpCode.GAME_RESULT, "WIN"))
            else:
                # P2가 나감 -> P1 승리
                self.p1.send_packet(encode_line(OpCode.GAME_RESULT, "WIN"))
                self.p2.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))

            self.p1.current_game = None
            self.p2.current_game = None

    # ----------------------
    # 헬퍼들
    # ----------------------
    def _action_from_code(self, code: ActionCode) -> Action:
        mapping = {
            ActionCode.LEFT: Action.LEFT,
            ActionCode.RIGHT: Action.RIGHT,
            ActionCode.ROTATE: Action.ROTATE,
            ActionCode.SOFT_DROP: Action.SOFT_DROP,
            ActionCode.HARD_DROP: Action.HARD_DROP,
        }
        return mapping.get(code, Action.NONE)

    def _encode_board(self, board: List[List[int]]) -> str:
        # 각 행을 숫자 문자열로 만들어 '/'로 이어붙임
        rows = []
        for row in board:
            rows.append("".join(str(min(cell, 9)) for cell in row))
        return "/".join(rows)

    def _broadcast_state(self, s1, s2):
        b1 = self._encode_board(s1.board)
        b2 = self._encode_board(s2.board)
        packet = encode_line(
            OpCode.GAME_STATE,
            str(self.id),
            str(self.p1.player_id),
            str(s1.score),
            str(s1.lines_cleared),
            "1" if s1.game_over else "0",
            b1,
            str(self.p2.player_id),
            str(s2.score),
            str(s2.lines_cleared),
            "1" if s2.game_over else "0",
            b2,
        )
        self.p1.send_packet(packet)
        self.p2.send_packet(packet)

    def _finish_game_locked(self, s1, s2):
        if self.finished:
            return
        self.finished = True
        self.alive = False

        # 간단한 승패 규칙: game_over 아닌 쪽 승리
        if s1.game_over and not s2.game_over:
            self.p1.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))
            self.p2.send_packet(encode_line(OpCode.GAME_RESULT, "WIN"))
        elif s2.game_over and not s1.game_over:
            self.p1.send_packet(encode_line(OpCode.GAME_RESULT, "WIN"))
            self.p2.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))
        else:
            # 동시 패배: 둘 다 LOSE
            self.p1.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))
            self.p2.send_packet(encode_line(OpCode.GAME_RESULT, "LOSE"))

        self.p1.current_game = None
        self.p2.current_game = None


class GameManager:
    """
    GameSession들을 관리하는 매니저.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.sessions: Dict[int, GameSession] = {}
        self._next_game_id = 1

    def _new_game_id(self) -> int:
        with self.lock:
            gid = self._next_game_id
            self._next_game_id += 1
        return gid

    def create_game(self, p1: "ClientSession", p2: "ClientSession") -> int:
        game_id = self._new_game_id()
        session = GameSession(game_id, p1, p2)
        with self.lock:
            self.sessions[game_id] = session
        p1.current_game = session
        p2.current_game = session
        session.start()
        return game_id

    def handle_input(self, player: "ClientSession", game_id: int, code: ActionCode):
        """
        서버가 입력 패킷을 받으면 즉시 해당 세션에 전달.
        """
        with self.lock:
            session = self.sessions.get(game_id)
        if not session:
            return
        session.apply_input(player.player_id, code)

    # [NEW] 포기 처리 메서드 추가
    def handle_leave(self, player: "ClientSession", game_id: int):
        with self.lock:
            session = self.sessions.get(game_id)
        if session:
            session.player_leave(player.player_id)