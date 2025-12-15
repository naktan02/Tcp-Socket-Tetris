import sys
import os
import time
from src.client.scenes.base_scene import BaseScene
from src.common.protocol import Packet
from src.common.constants import CMD_RES_LOGIN, CMD_REQ_SEARCH_ROOM
from src.client.network.router import route

try:
    import msvcrt
except ImportError:
    import select
    import tty
    import termios
    msvcrt = None

class LoginScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # 상태 정의 (State Machine)
        self.STATE_INPUT_IP = 0      # IP 입력 중
        self.STATE_INPUT_NICK = 1    # 닉네임 입력 중
        self.STATE_CONNECTING = 2    # 연결 시도 중 (대기)
        
        self.current_state = self.STATE_INPUT_IP
        self.input_buffer = ""       # 현재 타이핑 중인 문자열 저장소
        
        # 입력받은 결과 저장
        self.target_ip = "127.0.0.1"
        self.nickname = "Player"
        
        self.connect_start_time = 0

    def on_enter(self):
        """
        [초기화] 씬에 진입할 때 호출.
        더 이상 여기서 input()을 호출하여 멈추지 않습니다.
        변수만 리셋하고 바로 리턴하여 update() 루프가 돌게 합니다.
        """
        self.current_state = self.STATE_INPUT_IP
        self.input_buffer = ""
        self.renderer.clear_screen()
        # 안내 문구 한번 출력
        print("=== TETRIS ONLINE ===")
        print("Server IP (Default 127.0.0.1): ", end='', flush=True)

    def update(self):
        """매 프레임 호출되어 키 입력을 감시하고 화면을 갱신합니다."""
        
        # 1. 연결 시도 중일 때는 타임아웃 체크만 하고 입력은 무시
        if self.current_state == self.STATE_CONNECTING:
            if time.time() - self.connect_start_time > 5: # 5초 타임아웃
                print("\n[Error] Connection/Login Timeout.")
                self._reset_to_ip_input()
            return

        # 2. 키보드 입력 처리 (Non-blocking)
        char = self._get_key_input()
        
        if char:
            self._process_char(char)

    def _get_key_input(self):
        """OS별 논블로킹 문자 입력 처리"""
        if os.name == 'nt' and msvcrt:
            if msvcrt.kbhit():
                # 특수 키 등은 제외하고 일반 문자만 받음
                ch = msvcrt.getch()
                return ch
        else:
            # Unix/Mac 계열 select 사용
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read(1).encode()
        return None

    def _process_char(self, char_bytes):
        """입력된 한 글자를 처리하는 로직"""
        try:
            # 1. Enter 키 처리 (\r 또는 \n)
            if char_bytes in (b'\r', b'\n'):
                print() # 줄바꿈
                self._on_enter_pressed()
                return

            # 2. Backspace 키 처리 (\x08 또는 \x7f)
            if char_bytes in (b'\x08', b'\x7f'):
                if len(self.input_buffer) > 0:
                    self.input_buffer = self.input_buffer[:-1]
                    # 콘솔에서 지우는 효과 (커서 뒤로 -> 공백 -> 커서 뒤로)
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                return

            # 3. 일반 문자 입력
            char_str = char_bytes.decode('utf-8')
            if char_str.isprintable():
                self.input_buffer += char_str
                # 화면에 입력된 글자 출력 (에코)
                print(char_str, end='', flush=True)
                
        except UnicodeDecodeError:
            pass

    def _on_enter_pressed(self):
        """엔터를 쳤을 때 상태 전환"""
        if self.current_state == self.STATE_INPUT_IP:
            # IP 입력 완료 -> 닉네임 입력으로 전환
            ip_in = self.input_buffer.strip()
            if ip_in:
                self.target_ip = ip_in
            else:
                self.target_ip = "127.0.0.1" # 기본값
            
            print(f"Set IP: {self.target_ip}")
            
            # 다음 상태 준비
            self.current_state = self.STATE_INPUT_NICK
            self.input_buffer = ""
            print("Nickname: ", end='', flush=True)
            
        elif self.current_state == self.STATE_INPUT_NICK:
            # 닉네임 입력 완료 -> 접속 시도
            nick_in = self.input_buffer.strip()
            if nick_in:
                self.nickname = nick_in
            else:
                self.nickname = "Player"
                
            self._start_connection()

    def _start_connection(self):
        """서버 연결 및 로그인 패킷 전송"""
        self.current_state = self.STATE_CONNECTING
        self.connect_start_time = time.time()
        print(f"Connecting to {self.target_ip}...")
        
        # 네트워크 연결 시도
        if self.network.connect(self.target_ip, 5000):
            # 연결 성공 시 로그인 패킷 전송
            self.network.login(self.nickname)
        else:
            print("[Error] Connection Failed.")
            self._reset_to_ip_input()

    def _reset_to_ip_input(self):
        """실패 시 다시 IP 입력 단계로 복귀"""
        time.sleep(1)
        self.on_enter() # 초기화 재호출

    @route(CMD_RES_LOGIN)
    def on_login_response(self, pkt):
        """서버로부터 로그인 응답이 왔을 때 (라우터에 의해 자동 호출)"""
        if pkt.body[0] == 0: # 성공
            print("Login Success!")
            # 로비 데이터 요청 후 씬 전환
            self.context.server_ip = self.target_ip
            self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
            self.manager.change_scene("LOBBY")
        else:
            print("Login Failed (Nickname taken or Server error).")
            self._reset_to_ip_input()