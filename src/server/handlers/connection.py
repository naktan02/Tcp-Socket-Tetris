# src/server/handlers/connection.py
from src.server.router import router
from src.common.constants import CMD_REQ_LOGIN, CMD_RES_LOGIN
from src.common.protocol import Packet

@router.route(CMD_REQ_LOGIN)
def handle_login(client, packet):
    """
    로그인 요청 처리
    [BODY]: Nickname (String)
    """
    try:
        nickname = packet.body.decode('utf-8')
        client.nickname = nickname
        client.is_authenticated = True
        
        print(f"[Login] {nickname} connected from {client.addr}")
        
        # 로그인 성공 응답 전송 (Result: 0=성공)
        # 구조: [LEN][CMD][Result(1B)]
        response = Packet(CMD_RES_LOGIN, bytes([0]))
        client.send_packet(response)
        
    except UnicodeDecodeError:
        print(f"[Error] Invalid nickname encoding from {client.addr}")