import os
import sys

# --- 화면 제어 함수 ---

def clear_screen():
    """커서를 상단으로 이동 (깜빡임 최소화)"""
    print("\033[H", end="")

def full_clear():
    """화면 전체 지우기 (로비 진입 시 등)"""
    os.system('cls' if os.name == 'nt' else 'clear')

# --- 그리기 함수 ---

def draw_header(title: str):
    print("=" * 40)
    print(f"{title:^40}") # 가운데 정렬
    print("=" * 40)

def draw_lobby(my_id: int | None, name: str, users: list[tuple[int, str]]):
    # 버퍼링: 문자열을 모아서 한 번에 출력
    buffer = []
    
    # 헤더
    buffer.append("=" * 40)
    buffer.append(f"{'뿌요뿌요 테트리스 - 로비':^40}")
    my_info = f"(나: {name}#{my_id})" if my_id else ""
    buffer.append(f"{my_info:^40}")
    buffer.append("=" * 40 + "\n")

    buffer.append("[ 접속자 목록 ]")
    if not users:
        buffer.append("  (없음)")
    else:
        for idx, (uid, uname) in enumerate(users, 1):
            me = " (나)" if my_id == uid else ""
            buffer.append(f"  {idx}. [{uid}] {uname}{me}")
    
    buffer.append("\n" + "-" * 40)
    buffer.append("[명령] 번호: 대결신청 | q: 종료")
    
    clear_screen()
    print("\n".join(buffer))

def draw_message(msg: str):
    print(f"\n[알림] {msg}")

def draw_game(
    my_role: str,
    opponent_name: str,
    scores: dict,
    my_board: list,
    op_board: list,
    game_over_msg: str | None = None,
):
    """
    game_ui.py에서 이미 가공된 데이터를 받아 출력만 담당
    """
    my_score = scores.get(my_role, 0)
    # 상대방 역할 구하기
    op_role = 'p1' if my_role == 'p2' else 'p2'
    op_score = scores.get(op_role, 0)

    buffer = []
    
    # 상단 점수판
    title = f"ME({my_role}) [{my_score}]  VS  [{op_score}] OPP({opponent_name})"
    buffer.append("=" * 60)
    buffer.append(f"{title:^60}")
    buffer.append("-" * 60)

    # 보드 출력
    # my_board, op_board는 이미 [['.', '■', ...], ...] 형태임
    for r in range(20):
        row_my = " ".join(my_board[r])
        row_op = " ".join(op_board[r])
        buffer.append(f"| {row_my} |   | {row_op} |")
    
    buffer.append("=" * 60)

    # 하단 메시지
    if game_over_msg:
        buffer.append(f"\n>>> {game_over_msg} <<<")
    else:
        buffer.append("\n[조작] WASD/IJKL:이동 | Space:드롭 | Q:기권")

    clear_screen()
    print("\n".join(buffer))