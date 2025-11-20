from __future__ import annotations
import threading
from typing import Dict, List

from common.protocol import OpCode, encode_line
from common.types import PlayerInfo
from common.constants import ROLE_P1, ROLE_P2


class Lobby:
    def __init__(self, server: "Server"):
        self.server = server
        self.players: Dict[int, "ClientSession"] = {}
        self.lock = threading.Lock()

    def add_player(self, session: "ClientSession"):
        with self.lock:
            self.players[session.player_id] = session

    def remove_player(self, session: "ClientSession"):
        with self.lock:
            self.players.pop(session.player_id, None)

    def get_players(self) -> List[PlayerInfo]:
        with self.lock:
            return [
                PlayerInfo(id=s.player_id, name=s.name)
                for s in self.players.values()
                if s.alive
            ]

    def get_session(self, player_id: int) -> "ClientSession | None":
        with self.lock:
            return self.players.get(player_id)

    def broadcast_user_list(self):
        players = self.get_players()
        fields = [OpCode.USER_LIST]
        for p in players:
            fields.append(str(p.id))
            fields.append(p.name)
        packet = encode_line(*fields)
        for s in list(self.players.values()):
            if s.alive:
                s.send_packet(packet)

    def handle_challenge(self, from_session: "ClientSession", payload: list[str]):
        if not payload:
            return
        try:
            target_id = int(payload[0])
        except ValueError:
            return
        target = self.get_session(target_id)
        if not target or not target.alive or target is from_session:
            from_session.send_packet(encode_line(OpCode.CHALLENGE_RESULT, "NO"))
            return
        target.send_packet(
            encode_line(
                OpCode.CHALLENGE_FROM, str(from_session.player_id), from_session.name
            )
        )

    def handle_challenge_reply(self, from_session: "ClientSession", payload: list[str]):
        if len(payload) < 2:
            return
        try:
            challenger_id = int(payload[0])
        except ValueError:
            return
        result = payload[1]
        challenger = self.get_session(challenger_id)
        if not challenger or not challenger.alive:
            return
        if result != "OK":
            challenger.send_packet(encode_line(OpCode.CHALLENGE_RESULT, "NO"))
            return
        # OK -> 게임 생성
        game_id = self.server.game_manager.create_game(challenger, from_session)
        challenger.send_packet(
            encode_line(
                OpCode.GAME_START, str(game_id), ROLE_P1, from_session.name
            )
        )
        from_session.send_packet(
            encode_line(
                OpCode.GAME_START, str(game_id), ROLE_P2, challenger.name
            )
        )
        challenger.send_packet(encode_line(OpCode.CHALLENGE_RESULT, "OK"))
        from_session.send_packet(encode_line(OpCode.CHALLENGE_RESULT, "OK"))
        self.broadcast_user_list()
