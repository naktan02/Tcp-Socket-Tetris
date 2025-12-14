# src/client/input_handler.py
import sys
import os

# Windows와 Mac/Linux의 입력 방식이 달라서 분기 처리
if os.name == 'nt':
    import msvcrt
else:
    import select
    import tty
    import termios

from src.common.constants import Action

class InputHandler:
    def __init__(self):
        # 키 매핑: 키보드 입력 -> Action 변환
        # WASD 제거하고 화살표 키만 사용
        self.key_map = {
            b' ': Action.DROP,       # 스페이스바: 하드 드롭
            b'q': Action.QUIT,       # Q: 종료
            
            # Windows 화살표 키 (접두사 0xe0 또는 0x00 뒤에 오는 코드)
            b'H': Action.ROTATE,     # Up Arrow    -> 회전
            b'K': Action.MOVE_LEFT,  # Left Arrow  -> 왼쪽 이동
            b'M': Action.MOVE_RIGHT, # Right Arrow -> 오른쪽 이동
            b'P': Action.DOWN        # Down Arrow  -> 아래로 이동 (소프트 드롭)
        }

    def get_action(self):
        """논-블로킹(Non-blocking)으로 키 입력을 확인하고 Action 반환"""
        if os.name == 'nt':
            return self._get_action_windows()
        else:
            return self._get_action_unix()

    def _get_action_windows(self):
        # 키가 눌렸는지 확인 (kbhit)
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            # 화살표 키 등 특수 키는 2바이트로 들어옴 (0xe0 또는 0x00 + 키코드)
            if key in (b'\x00', b'\xe0'):
                try:
                    key = msvcrt.getch() # 실제 키 코드 읽기
                    return self.key_map.get(key, None)
                except ValueError:
                    return None
            
            # 일반 키 (Space, q 등)
            return self.key_map.get(key, None)
        return None

    def _get_action_unix(self):
        # Mac/Linux용 구현 (필요시 추가)
        return None