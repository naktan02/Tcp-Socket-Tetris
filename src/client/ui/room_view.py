# src/client/ui/room_view.py
from src.common.constants import *
from src.common.config import MAX_ROOM_SLOTS

class RoomView:
    def __init__(self):
        self.BORDER_H = "─"
        self.BORDER_V = "│"
        self.CORNER_TL = "┌"
        self.CORNER_TR = "┐"
        self.CORNER_BL = "└"
        self.CORNER_BR = "┘"
        self.TEE_L = "├"
        self.TEE_R = "┤"

    def draw(self, room_id, slots, ready_states, my_slot):
        """대기실 화면 라인 생성"""
        lines = []
        width = 40
        
        # 상단
        lines.append(f"{self.CORNER_TL}{self.BORDER_H * width}{self.CORNER_TR}")
        msg = f"ROOM #{room_id} - WAITING..."
        lines.append(f"{self.BORDER_V} {msg}".ljust(width+1) + f"{self.BORDER_V}")
        lines.append(f"{self.TEE_L}{self.BORDER_H * width}{self.TEE_R}")
        lines.append(f"{self.BORDER_V}" + " "*width + f"{self.BORDER_V}")
        
        # 슬롯
        for i in range(MAX_ROOM_SLOTS):
            status = "EMPTY"
            color = COLOR_GRAY
            name = "..."
            
            if i < len(slots) and slots[i]:
                name = slots[i]
                if i == 0:
                    status = "HOST"
                    color = COLOR_CYAN
                elif i < len(ready_states) and ready_states[i]:
                    status = "READY!"
                    color = COLOR_GREEN
                else:
                    status = "WAITING"
                    color = COLOR_YELLOW
                
                if i == my_slot:
                    name += " (ME)"
            
            info = f" [Slot {i+1}] {name}".ljust(25) + f"{color}{status}{COLOR_RESET}"
            visible_len = len(f" [Slot {i+1}] {name}") + len(status) + (25 - len(f" [Slot {i+1}] {name}"))
            padding = width - visible_len
            
            lines.append(f"{self.BORDER_V} {info}" + " "*(padding-1) + f"{self.BORDER_V}")

        lines.append(f"{self.BORDER_V}" + " "*width + f"{self.BORDER_V}")
        lines.append(f"{self.TEE_L}{self.BORDER_H * width}{self.TEE_R}")
        
        action_msg = "[Space] Start Game" if my_slot == 0 else "[Space] Toggle Ready"
        lines.append(f"{self.BORDER_V} {action_msg}   [Q] Leave".ljust(width+1) + f"{self.BORDER_V}")
        lines.append(f"{self.CORNER_BL}{self.BORDER_H * width}{self.CORNER_BR}")
        
        lines.append(" " * 50) 
        
        return lines