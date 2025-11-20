import threading
from common.protocol import OpCode
from client.renderer import draw_message

class Receiver(threading.Thread):
    def __init__(self, conn, lobby_ui, lobby_state):
        super().__init__(daemon=True)
        self.conn = conn
        self.lobby_ui = lobby_ui
        self.lobby_state = lobby_state
        
        # 게임 중일 때만 여기에 GameUI 인스턴스가 들어감
        self.game_ui = None 
        
        self.alive = True

        self.handlers = {
            OpCode.LOGIN_OK: self.lobby_ui.handle_login_ok,
            OpCode.USER_LIST: self.lobby_ui.handle_user_list,
            OpCode.CHALLENGE_FROM: self.lobby_ui.handle_challenge_from,
            OpCode.CHALLENGE_RESULT: self.lobby_ui.handle_challenge_result,
            OpCode.GAME_START: self.lobby_ui.handle_game_start,
            OpCode.GAME_STATE: self._handle_game_state,     # 변경됨
            OpCode.GAME_RESULT: self._handle_game_result,   # 변경됨
        }

    def set_game_ui(self, game_ui):
        """메인에서 게임 시작 시 UI를 연결해줌"""
        self.game_ui = game_ui

    def run(self):
        while self.alive and self.conn.alive:
            parts = self.conn.recv_packet()
            if parts is None:
                break
            opcode = parts[0]
            payload = parts[1:]

            handler = self.handlers.get(opcode)
            if handler:
                handler(payload)

    def _handle_game_state(self, payload):
        # 게임 중일 때만 처리
        if self.game_ui:
            self.game_ui.handle_game_state(payload)

    def _handle_game_result(self, payload):
        # 게임 중일 땐 게임 UI에 결과 전달
        if self.game_ui:
            self.game_ui.handle_game_over(payload)
        else:
            self.lobby_ui.handle_game_result(payload)