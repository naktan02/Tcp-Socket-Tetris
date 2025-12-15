# src/common/constants.py
from enum import Enum, auto

# --- Protocol Commands (PPT 명세 기반) ---
# 접속 (0x00 ~ 0x0F)
CMD_REQ_LOGIN = 0x01
CMD_RES_LOGIN = 0x02

# 방 관리 (0x10 ~ 0x1F)
CMD_REQ_SEARCH_ROOM = 0x10
CMD_REQ_CREATE_ROOM = 0x11
CMD_RES_CREATE_ROOM = 0x12
CMD_REQ_JOIN_ROOM   = 0x13
CMD_RES_JOIN_ROOM   = 0x14
CMD_NOTI_ENTER_ROOM = 0x15
CMD_REQ_LEAVE_ROOM  = 0x16
CMD_NOTI_LEAVE_ROOM = 0x17
CMD_REQ_ROOM_INFO   = 0x18

# 게임 상태 (0x20 ~ 0x2F)
CMD_REQ_TOGGLE_READY = 0x20
CMD_NOTI_READY_STATE = 0x21
CMD_NOTI_GAME_START  = 0x22  # 시드 포함

# 조작 (0x30 ~ 0x3F)
CMD_REQ_MOVE = 0x30
CMD_NOTI_MOVE = 0x31

# 상호작용 (0x40 ~ 0x4F)
CMD_REQ_ATTACK   = 0x40
CMD_NOTI_GARBAGE = 0x41

# 종료 (0x90 ~ 0x9F)
CMD_REQ_GAMEOVER = 0x90
CMD_NOTI_RESULT  = 0x91

# --- Input Actions (추상화된 입력) ---
class Action(Enum):
    MOVE_LEFT  = 1
    MOVE_RIGHT = 2
    ROTATE     = 3 # 시계 방향
    DOWN       = 4 # 소프트 드롭
    DROP       = 5 # 하드 드롭
    HOLD       = 6
    USE_ITEM   = 7
    QUIT       = 99

# --- ANSI Colors (화면 출력용) ---
COLOR_RESET  = "\033[0m"
COLOR_RED    = "\033[31m"
COLOR_GREEN  = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE   = "\033[34m"
COLOR_MAGENTA= "\033[35m"
COLOR_CYAN   = "\033[36m"
COLOR_WHITE  = "\033[37m"
COLOR_GRAY   = "\033[90m"


BLOCK_COLOR_MAP = {
    1: COLOR_CYAN,    # I 미노
    2: COLOR_YELLOW,  # O 미노
    3: COLOR_MAGENTA, # T 미노
    4: COLOR_GREEN,   # S 미노
    5: COLOR_RED,     # Z 미노
    6: COLOR_BLUE,    # J 미노
    7: COLOR_WHITE,   # L 미노 (주황색이 없으므로 흰색 대체)
    8: "\033[90m",    # Garbage (회색)
}