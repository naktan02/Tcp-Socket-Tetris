# src/client/scenes/base_scene.py
class BaseScene:
    def __init__(self, manager):
        self.manager = manager
        self.network = manager.network
        self.renderer = manager.renderer
        self.input_handler = manager.input_handler
        self._handlers = {}
        self._register_handlers()

    def update(self):
        """매 프레임 호출되는 로직"""
        pass

    def render(self):
        """매 프레임 호출되는 렌더링"""
        pass

    def _register_handlers(self):
        """
        현재 클래스(self)의 모든 메서드를 검사하여
        @route(CMD) 데코레이터가 붙은 메서드를 _handlers 딕셔너리에 등록
        """
        # dir(self)는 객체의 모든 속성/메서드 이름을 반환
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            # 메서드에 '_cmd_id'라는 꼬리표가 있는지 확인
            if hasattr(method, '_cmd_id'):
                cmd_id = method._cmd_id
                self._handlers[cmd_id] = method

    def handle_packet(self, packet):
        """
        패킷의 CMD를 보고 등록된 핸들러 메서드를 자동 실행
        """
        handler = self._handlers.get(packet.cmd)
        if handler:
            handler(packet)
        else:
            # 핸들러가 없으면 무시하거나 로그 출력
            pass

    def on_enter(self):
        """씬 진입 시 호출"""
        pass

    def on_exit(self):
        """씬 종료 시 호출"""
        pass
