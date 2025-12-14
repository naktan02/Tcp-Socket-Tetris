# src/client/scenes/login_scene.py
import time
from src.client.scenes.base_scene import BaseScene
from src.common.constants import CMD_RES_LOGIN, CMD_REQ_SEARCH_ROOM
from src.common.protocol import Packet
from src.client.router import route

class LoginScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.tried_login = False

    def on_enter(self):
        self.renderer.clear_screen()
        print("=== TETRIS ONLINE ===")
        
        # 1. IP 입력 (Blocking)
        ip = input("Server IP (Default 127.0.0.1): ").strip()
        if not ip: ip = "127.0.0.1"
        
        print(f"Connecting to {ip}...")
        if not self.network.connect(ip, 5000):
            print("Connection failed. Check IP and try again.")
            time.sleep(2)
            # 재시도 로직이 필요하지만, 여기선 단순히 종료하거나 다시 입력받게 할 수 있음
            # 구조상 매니저가 다시 LoginScene을 유지하므로 루프
            return

        # 2. 닉네임 입력
        nick = input("Nickname: ").strip()
        if not nick: nick = "Player"
        
        self.network.login(nick)
        self.login_start_time = time.time()
        self.tried_login = True

    def update(self):
        if not self.tried_login:
            # 연결 실패 후 update가 불리면 다시 시도? 
            # 편의상 실패하면 다시 on_enter 호출하는 식으로 처리 가능
            # 여기선 생략
            pass

        # 로그인 응답 대기 (Timeout 5초)
        if time.time() - self.login_start_time > 5:
            print("Login timeout.")
            self.manager.running = False # 종료
            return

    @route(CMD_RES_LOGIN)
        def on_login_response(self, pkt):
            if pkt.body[0] == 0:
                # 로그인 성공 -> 로비로 이동
                # 목록 요청
                self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
                self.manager.change_scene("LOBBY")
            else:
                print("Login failed.")
                self.manager.running = False
