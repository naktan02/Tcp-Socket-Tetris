# src/client/core/scene_manager.py
from src.client.renderer import Renderer
from src.client.input_handler import InputHandler
from src.client.network_client import NetworkClient
from src.client.scenes.login_scene import LoginScene
from src.client.scenes.lobby_scene import LobbyScene
from src.client.scenes.room_scene import RoomScene
from src.client.scenes.game_scene import GameScene

class SceneManager:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.network = NetworkClient()
        
        self.running = True
        
        # 공유 데이터
        self.my_slot = -1
        self.room_id = -1
        self.game_seed = 0
        self.game_players = []

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
            # 1. 네트워크 패킷 처리 (공통)
            # 씬 별로 처리하고 싶다면 manager가 loop 돌면서 current_scene 에 넘김
            while True:
                pkt = self.network.get_packet()
                if not pkt: break
                self.current_scene.handle_packet(pkt)
            
            # 2. 씬 업데이트
            self.current_scene.update()
        
        self.network.disconnect()
