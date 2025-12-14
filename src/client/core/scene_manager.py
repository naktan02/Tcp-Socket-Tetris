# src/client/core/scene_manager.py
from src.client.core.renderer import Renderer
from src.client.core.input_handler import InputHandler
from src.client.network.network_client import NetworkClient
from src.client.scenes.login_scene import LoginScene
from src.client.scenes.lobby_scene import LobbyScene
from src.client.scenes.room_scene import RoomScene
from src.client.scenes.game_scene import GameScene
from src.client.core.session_context import SessionContext  

class SceneManager:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.network = NetworkClient()
        
        self.running = True
        self.context = SessionContext()

        # 씬 등록
        self.scenes = {
            "LOGIN": LoginScene(self),
            "LOBBY": LobbyScene(self),
            "ROOM": RoomScene(self),
            "GAME": GameScene(self)
        }
        self.current_scene = self.scenes["LOGIN"]
        self.current_scene.on_enter()

    def change_scene(self, scene_name):
        if scene_name in self.scenes:
            self.current_scene.on_exit()
            self.current_scene = self.scenes[scene_name]
            self.current_scene.on_enter()

    def run(self):
        while self.running:
            # 1. 네트워크 패킷 처리
            while True:
                pkt = self.network.get_packet()
                if not pkt: break
                self.current_scene.handle_packet(pkt)
            
            # 2. 씬 업데이트
            self.current_scene.update()
        
        self.network.disconnect()