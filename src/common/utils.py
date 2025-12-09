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