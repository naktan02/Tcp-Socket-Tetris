# main_server.py
import sys
import os

# 프로젝트 루트 경로를 sys.path에 추가 (src 패키지 인식용)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.server.infra.server_core import TetrisServer

def main():
    try:
        # 서버 인스턴스 생성 및 시작
        server = TetrisServer()
        server.start()
    except KeyboardInterrupt:
        print("\n[Main] Server stopped by user.")
    except Exception as e:
        print(f"\n[Main] Server Error: {e}")

if __name__ == "__main__":
    main()