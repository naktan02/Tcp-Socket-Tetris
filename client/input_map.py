from common.constants import ROLE_P1, ROLE_P2
from common.types import ActionCode


def get_keymap(role: str):
    """
    역할에 따라 문자 -> ActionCode 매핑.
    (엔터로 한 줄 입력 받기 때문에 간단한 문자 위주)
    """
    if role == ROLE_P1:
        # WASD + space
        return {
            "a": ActionCode.LEFT,
            "d": ActionCode.RIGHT,
            "w": ActionCode.ROTATE,
            "s": ActionCode.SOFT_DROP,
            " ": ActionCode.HARD_DROP,
        }
    elif role == ROLE_P2:
        # IJKL + space
        return {
            "j": ActionCode.LEFT,
            "l": ActionCode.RIGHT,
            "i": ActionCode.ROTATE,
            "k": ActionCode.SOFT_DROP,
            " ": ActionCode.HARD_DROP,
        }
    else:
        # 기본값: P1처럼
        return {
            "a": ActionCode.LEFT,
            "d": ActionCode.RIGHT,
            "w": ActionCode.ROTATE,
            "s": ActionCode.SOFT_DROP,
            " ": ActionCode.HARD_DROP,
        }
