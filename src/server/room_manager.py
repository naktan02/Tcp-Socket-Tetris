# src/server/room_manager.py
from typing import Dict
from .room import Room

class RoomManager:
    def __init__(self):
        self._rooms: Dict[int, Room] = {}
        self._next_room_id = 1

    def create_room(self, title: str) -> Room:
        """새로운 방 생성"""
        room_id = self._next_room_id
        self._next_room_id += 1
        
        new_room = Room(room_id, title)
        self._rooms[room_id] = new_room
        return new_room

    def get_room(self, room_id: int) -> Room:
        return self._rooms.get(room_id)

    def remove_room(self, room_id: int):
        if room_id in self._rooms:
            del self._rooms[room_id]

    def get_all_rooms(self):
        return list(self._rooms.values())

# 전역 관리자 객체 생성
room_manager = RoomManager()