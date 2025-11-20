DELIM = "|"
ENCODING = "utf-8"


class OpCode:
    LOGIN = "LOGIN"                  # C->S: LOGIN|name
    LOGIN_OK = "LOGIN_OK"            # S->C: LOGIN_OK|player_id|name

    USER_LIST = "USER_LIST"          # S->C: USER_LIST|id1|name1|id2|name2|...

    CHALLENGE = "CHALLENGE"          # C->S: CHALLENGE|target_id
    CHALLENGE_FROM = "CHALLENGE_FROM"  # S->C: CHALLENGE_FROM|from_id|from_name
    CHALLENGE_REPLY = "CHALLENGE_REPLY"  # C->S: CHALLENGE_REPLY|from_id|OK/NO
    CHALLENGE_RESULT = "CHALLENGE_RESULT"  # S->C: CHALLENGE_RESULT|OK/NO

    GAME_START = "GAME_START"        # S->C: GAME_START|game_id|role|opponent_name

    GAME_INPUT = "GAME_INPUT"        # C->S: GAME_INPUT|game_id|player_id|action_code
    GAME_STATE = "GAME_STATE"        # S->C: GAME_STATE|...
    GAME_RESULT = "GAME_RESULT"      # S->C: GAME_RESULT|WIN/LOSE
    
    GAME_LEAVE = "GAME_LEAVE"        # [NEW] C->S: GAME_LEAVE (게임 중도 포기)

    PING = "PING"
    PONG = "PONG"


def encode_line(*fields: str) -> bytes:
    line = DELIM.join(fields) + "\n"
    return line.encode(ENCODING)


def decode_line(data: bytes):
    text = data.decode(ENCODING).rstrip("\n")
    return text.split(DELIM)