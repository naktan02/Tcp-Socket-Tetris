from __future__ import annotations
import threading

from common.protocol import OpCode, decode_line, encode_line
from common.types import ActionCode


class ClientSession(threading.Thread):
    def __init__(self, server: "Server", conn, addr):
        super().__init__(daemon=True)
        self.server = server
        self.conn = conn
        self.addr = addr
        self.file = conn.makefile("rb")
        self.alive = True
        self.lock = threading.Lock()

        self.player_id = server.next_player_id()
        self.name = f"Player{self.player_id}"
        self.current_game = None  # GameSession

        # --- 패턴: opcode -> handler 디스패처 ---
        self.handlers = {
            OpCode.CHALLENGE: self._handle_challenge,
            OpCode.CHALLENGE_REPLY: self._handle_challenge_reply,
            OpCode.GAME_INPUT: self._handle_game_input,
            OpCode.GAME_LEAVE: self._handle_game_leave,  # [NEW] 핸들러 등록
            OpCode.PING: self._handle_ping,
        }

    def send_packet(self, packet: bytes):
        with self.lock:
            try:
                self.conn.sendall(packet)
            except OSError:
                self.alive = False

    def close(self):
        self.alive = False
        try:
            self.conn.close()
        except OSError:
            pass

    def run(self):
        print(f"[SERVER] New connection {self.addr}, temp id={self.player_id}")
        try:
            # 로그인 먼저
            line = self.file.readline()
            if not line:
                self._cleanup()
                return
            parts = decode_line(line)
            if len(parts) < 2 or parts[0] != OpCode.LOGIN:
                self._cleanup()
                return
            name = parts[1].strip() or self.name
            self.name = name
            self.send_packet(
                encode_line(OpCode.LOGIN_OK, str(self.player_id), self.name)
            )
            self.server.lobby.add_player(self)
            self.server.lobby.broadcast_user_list()

            # 메인 루프
            while self.alive:
                line = self.file.readline()
                if not line:
                    break
                parts = decode_line(line)
                if not parts:
                    continue
                opcode = parts[0]
                payload = parts[1:]
                handler = self.handlers.get(opcode)
                if handler:
                    handler(payload)
                # 알 수 없는 opcode는 무시
        except OSError:
            pass
        finally:
            self._cleanup()

    # ---------------- 핸들러들 ----------------

    def _handle_challenge(self, payload: list[str]):
        self.server.lobby.handle_challenge(self, payload)

    def _handle_challenge_reply(self, payload: list[str]):
        self.server.lobby.handle_challenge_reply(self, payload)

    def _handle_game_input(self, payload: list[str]):
        if len(payload) < 3:
            return
        try:
            game_id = int(payload[0])
            player_id = int(payload[1])
        except ValueError:
            return
        if player_id != self.player_id:
            return
        code_str = payload[2]
        try:
            code = ActionCode(code_str)
        except ValueError:
            return
        self.server.game_manager.handle_input(self, game_id, code)

    # [NEW] 게임 포기 처리 핸들러
    def _handle_game_leave(self, payload: list[str]):
        if self.current_game:
            self.server.game_manager.handle_leave(self, self.current_game.id)

    def _handle_ping(self, payload: list[str]):
        self.send_packet(encode_line(OpCode.PONG))

    # -------------------------------------------

    def _cleanup(self):
        print(f"[SERVER] Disconnect {self.name} ({self.player_id})")
        # 연결이 끊기면 게임 중이던 것도 포기 처리
        if self.current_game:
            self.server.game_manager.handle_leave(self, self.current_game.id)
        self.server.lobby.remove_player(self)
        self.server.lobby.broadcast_user_list()
        self.close()