# src/client/session_context.py

class SessionContext:
    """
    클라이언트의 게임 세션 데이터를 관리하는 클래스
    (Manager에서 데이터만 분리)
    """
    def __init__(self):
        self.my_slot = -1
        self.room_id = -1
        self.game_seed = 0
        self.game_players = []
        self.server_ip = "127.0.0.1"
        
    def reset_game_data(self):
        """방/게임 관련 데이터 초기화"""
        self.my_slot = -1
        self.room_id = -1
        self.game_seed = 0
        self.game_players = []