import sys
from client.config import SERVER_HOST, SERVER_PORT, DEFAULT_ROLE
from client.network import ClientConnection
from client.lobby_ui import LobbyUI, LobbyState
from client.game_ui import GameUI
from client.receiver import Receiver
from client.renderer import draw_message, full_clear

def main():
    name = input("닉네임 입력: ").strip() or "Player"
    
    conn = ClientConnection(SERVER_HOST, SERVER_PORT)

    lobby_state = LobbyState(name)
    lobby_ui = LobbyUI(conn, lobby_state)

    lobby_ui.send_login()

    receiver = Receiver(conn, lobby_ui, lobby_state)
    receiver.start()

    while True:
        game_info = lobby_ui.loop()
        
        if game_info is None:
            print("게임을 종료합니다.")
            conn.close()
            break

        # [수정 포인트] game_info 분해 및 GameUI 생성 시 my_id 전달
        game_id, my_role, opp_name = game_info
        
        # lobby_state.my_id(내 플레이어 ID)를 추가로 전달합니다.
        game_ui = GameUI(conn, game_id, lobby_state.my_id, my_role, opp_name)
        
        receiver.set_game_ui(game_ui)
        
        full_clear()
        game_ui.loop()

        receiver.set_game_ui(None)
        lobby_state.game_info = None
        lobby_state.game_result = None
        lobby_state.pending_from = None
        lobby_state.dirty = True
        
        draw_message("로비로 복귀했습니다. (잠시 대기)")

if __name__ == "__main__":
    main()