# src/server/router.py
from typing import Callable, Dict

class PacketRouter:
    def __init__(self):
        # CMD(int) -> Handler Function 매핑
        self.routes: Dict[int, Callable] = {}

    def route(self, cmd: int):
        """데코레이터: 특정 CMD를 처리할 핸들러 등록"""
        def decorator(func):
            self.routes[cmd] = func
            return func
        return decorator

    def handle(self, client, packet):
        """패킷을 받아서 적절한 핸들러 실행"""
        handler = self.routes.get(packet.cmd)
        if handler:
            # 핸들러 함수 호출 (client 객체와 패킷 본문 전달)
            handler(client, packet)
        else:
            print(f"[Warn] No handler for CMD: {hex(packet.cmd)}")

# 전역 라우터 객체 생성 (다른 파일에서 import router 해서 사용)
router = PacketRouter()