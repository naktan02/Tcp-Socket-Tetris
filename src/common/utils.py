import socket
import logging

def get_local_ip():
    """
    현재 컴퓨터가 외부와 통신할 때 사용하는 내부 IP 주소를 반환합니다.
    (예: 192.168.0.x)
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 실제로 연결하지는 않고, 구글 DNS(8.8.8.8)로 나가는 경로를 확인하여
        # 현재 활성화된 네트워크 인터페이스의 IP를 얻습니다.
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        # 네트워크가 연결되지 않은 경우 로컬호스트 반환
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def setup_logger(name):
    """
    간단한 로거 설정을 위한 헬퍼 함수
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def setup_file_logger(name):
    """
    [NEW] 파일 로깅을 위한 헬퍼 함수.
    게임 화면(UI)을 방해하지 않고 'game_debug.log' 파일에 로그를 기록합니다.
    """
    logger = logging.getLogger(name)
    # 핸들러가 이미 있다면 추가하지 않음 (중복 방지)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        # 파일 핸들러 생성 (append 모드)
        fh = logging.FileHandler('game_debug.log', encoding='utf-8')
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger