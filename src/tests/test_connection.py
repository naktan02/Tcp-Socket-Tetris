import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.client.network_client import NetworkClient
from src.common.constants import CMD_RES_LOGIN

def main():
    print("--- Client Connection Test ---")
    
    # 1. 클라이언트 생성
    client = NetworkClient()
    
    # 2. 서버 접속 시도 (로컬호스트)
    print("[1] Connecting to server...")
    if not client.connect('127.0.0.1', 5000):
        print("FAIL: Cannot connect to server.")
        return

    # 3. 로그인 요청 전송
    nickname = "TEST_USER"
    print(f"[2] Sending Login Request (Nickname: {nickname})...")
    client.login(nickname)

    # 4. 응답 대기 (최대 2초)
    print("[3] Waiting for response...")
    start_time = time.time()
    while time.time() - start_time < 2.0:
        pkt = client.get_packet()
        if pkt:
            print(f"\n[Success] Packet Received: {pkt}")
            if pkt.cmd == CMD_RES_LOGIN:
                print(">>> Login Approved! (Phase 3 Complete)")
            else:
                print(f">>> Received different command: {hex(pkt.cmd)}")
            break
        time.sleep(0.1)
    else:
        print("\n[Fail] No response from server.")

    # 5. 연결 종료
    client.disconnect()

if __name__ == "__main__":
    main()