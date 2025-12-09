# src/common/config.py

# 네트워크 설정
HOST = '0.0.0.0'       # 모든 인터페이스에서 접속 허용
PORT = 5000            # 서버 포트
BUFFER_SIZE = 4096     # 소켓 수신 버퍼 크기
TIMEOUT = 1.0          # 소켓 타임아웃 (초)

# 프로토콜 설정
HEADER_SIZE = 2        # [LEN] 필드의 크기 (2바이트)
encoding = 'utf-8'     # 문자열 인코딩 방식

# 게임 설정
TICK_RATE = 30         # 서버/클라이언트 로직 갱신 주기 (FPS)
RANDOM_SEED_SIZE = 4   # 시드값 크기 (4바이트 정수)

MAX_ROOM_SLOTS = 4  # 최대 방 인원수