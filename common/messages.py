from .protocol import OpCode, encode_line
from .types import ActionCode


def make_login(name: str) -> bytes:
    return encode_line(OpCode.LOGIN, name)


def make_challenge(target_id: int) -> bytes:
    return encode_line(OpCode.CHALLENGE, str(target_id))


def make_challenge_reply(from_id: int, ok: bool) -> bytes:
    return encode_line(
        OpCode.CHALLENGE_REPLY,
        str(from_id),
        "OK" if ok else "NO",
    )


def make_game_input(game_id: int, player_id: int, action: ActionCode) -> bytes:
    return encode_line(
        OpCode.GAME_INPUT,
        str(game_id),
        str(player_id),
        action.value,
    )

def make_leave_game() -> bytes:
    return encode_line(OpCode.GAME_LEAVE)