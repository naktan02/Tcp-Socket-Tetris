from typing import List, Tuple, Optional
import sys
import msvcrt  # Windows용 (맥/리눅스면 sys.stdin 등 별도 처리 필요)
import time

from common.messages import make_login, make_challenge, make_challenge_reply
from client.renderer import draw_lobby, draw_message, full_clear
class LobbyState:
    def __init__(self, name: str):
        self.name = name
        self.my_id: Optional[int] = None
        self.users: List[Tuple[int, str]] = []
        self.pending_from: Optional[Tuple[int, str]] = None
        self.game_info: Optional[Tuple[int, str, str]] = None
        self.game_result: Optional[str] = None
        self.dirty = True  # 화면 갱신 필요 여부 플래그

class LobbyUI:
    def __init__(self, conn, state: LobbyState):
        self.conn = conn
        self.state = state

    # --- 서버 패킷 핸들러 ---

    def handle_login_ok(self, payload: list[str]):
        self.state.my_id = int(payload[0])
        self.state.name = payload[1]
        self.state.dirty = True

    def handle_user_list(self, payload: list[str]):
        users: List[Tuple[int, str]] = []
        # payload: [id1, name1, id2, name2, ...]
        it = iter(payload)
        for pid, pname in zip(it, it):
            try:
                uid = int(pid)
            except ValueError:
                continue
            users.append((uid, pname))
        self.state.users = users
        self.state.dirty = True

    def handle_challenge_from(self, payload: list[str]):
        if len(payload) < 2:
            return
        from_id = int(payload[0])
        from_name = payload[1]
        self.state.pending_from = (from_id, from_name)
        self.state.dirty = True

    def handle_challenge_result(self, payload: list[str]):
        if not payload:
            return
        result = payload[0]
        if result == "OK":
            self.show_temporary_message("대결 수락됨! 게임 생성 중...")
        else:
            self.show_temporary_message("대결이 거절되었습니다.")
            self.state.pending_from = None  # 혹시 남아있을 상태 초기화
        self.state.dirty = True

    def handle_game_start(self, payload: list[str]):
        if len(payload) < 3:
            return
        game_id = int(payload[0])
        role = payload[1]
        opponent_name = payload[2]
        self.state.game_info = (game_id, role, opponent_name)
        self.state.dirty = True

    def handle_game_result(self, payload: list[str]):
        if payload:
            self.state.game_result = payload[0]
            self.show_temporary_message(f"게임 결과: {self.state.game_result}")
        self.state.dirty = True

    def send_login(self):
        self.conn.send(make_login(self.state.name))

    # --- 헬퍼 ---
    def show_temporary_message(self, msg: str, duration=1.5):
        """잠시 메시지를 보여주고 화면 갱신"""
        draw_message(msg)
        time.sleep(duration)
        self.state.dirty = True

    # --- 메인 루프 (비동기 입력) ---
    def loop(self):
        """
        input() 대신 msvcrt를 사용하여 멈추지 않고 입력을 받음.
        """
        full_clear()
        while True:
            # 1. 화면 갱신 (필요할 때만)
            if self.state.dirty:
                draw_lobby(self.state.my_id, self.state.name, self.state.users)
                
                # 대결 신청이 온 경우 추가 안내
                if self.state.pending_from:
                    fid, fname = self.state.pending_from
                    print(f"\n[!] {fname}#{fid} 님이 대결을 신청했습니다!")
                    print("    수락하려면 'y', 거절하려면 'n'을 누르세요.")
                else:
                    print("\n[조작] 번호키: 대결신청 | q: 종료")
                
                self.state.dirty = False

            # 2. 게임 매칭 완료 체크
            if self.state.game_info:
                return self.state.game_info

            # 3. 비동기 키 입력 처리
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                try:
                    key = ch.decode("utf-8").lower()
                except UnicodeDecodeError:
                    continue

                # [상황 A] 대결 신청을 받은 상태
                if self.state.pending_from:
                    if key == 'y':
                        fid, _ = self.state.pending_from
                        self.conn.send(make_challenge_reply(fid, True))
                        self.show_temporary_message("대결을 수락했습니다.")
                        self.state.pending_from = None
                    elif key == 'n':
                        fid, _ = self.state.pending_from
                        self.conn.send(make_challenge_reply(fid, False))
                        self.show_temporary_message("대결을 거절했습니다.")
                        self.state.pending_from = None
                    continue

                # [상황 B] 일반 로비 상태
                if key == 'q':
                    return None  # 종료
                
                # 숫자키 입력 (1~9) -> 해당 순서의 유저에게 대결 신청
                if key.isdigit() and key != '0':
                    idx = int(key) - 1
                    # 나 자신을 제외한 리스트를 보여주는게 좋지만, 
                    # 일단 전체 리스트 기준 인덱스로 처리
                    if 0 <= idx < len(self.state.users):
                        target_id, target_name = self.state.users[idx]
                        if target_id == self.state.my_id:
                            self.show_temporary_message("자기 자신에게는 신청할 수 없습니다.")
                        else:
                            self.conn.send(make_challenge(target_id))
                            self.show_temporary_message(f"{target_name}#{target_id} 에게 대결 신청을 보냈습니다.")

            time.sleep(0.05) # CPU 과점유 방지