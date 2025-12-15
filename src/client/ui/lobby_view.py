# src/client/ui/lobby_view.py
from src.common.constants import *

class LobbyView:
    def __init__(self):
        # 선 모양 정의
        self.BORDER_H = "─"
        self.BORDER_V = "│"
        self.CORNER_TL = "┌"
        self.CORNER_TR = "┐"
        self.CORNER_BL = "└"
        self.CORNER_BR = "┘"
        self.TEE_L = "├"
        self.TEE_R = "┤"

    def draw(self, room_list, server_ip= ""):
        lines = []
        width = 40
        
        lines.append(f"{self.CORNER_TL}{self.BORDER_H * width}{self.CORNER_TR}")
        title = f" {COLOR_YELLOW}TETRIS BATTLE ONLINE{COLOR_RESET}"
        ip_str = f"[{server_ip}]"
        ip_display = f"{COLOR_CYAN}{ip_str}{COLOR_RESET} "
        title_pure_len = 21
        ip_pure_len = len(ip_str) + 1
        padding = width - (title_pure_len + ip_pure_len)
        if padding < 0: padding = 0
        header_content = title + " " * padding + ip_display
        lines.append(f"{self.BORDER_V}{header_content}{self.BORDER_V}")
        lines.append(f"{self.TEE_L}{self.BORDER_H * width}{self.TEE_R}")
        lines.append(f"{self.BORDER_V} Available Rooms:".ljust(41) + f"{self.BORDER_V}")
        
        for i in range(10):
            if i < len(room_list):
                room = room_list[i]
                # [ID] [STATUS] Title 형태
                raw_status = room.get('status', 0)
                status_text = "WAIT" if raw_status == 0 else "PLAY"
                
                # 색상 처리
                s_color = COLOR_GREEN if status_text == 'WAIT' else COLOR_RED
                
                info = f" [{room['id']}] {room['title']} [{s_color}{status_text}{COLOR_RESET}]"
                
                # 길이 계산 (색상코드 제외)
                visible_len = len(f" [{room['id']}] {room['title']} [{status_text}]")
                
                if visible_len > width - 2:
                    # 너무 길면 자름 (단순화)
                    info = info[:width+5] # 색상코드 감안 대충 자름
                    
                # 패딩 계산
                pad_len = width - visible_len
                lines.append(f"{self.BORDER_V}{info}" + " " * max(0, pad_len) + f"{self.BORDER_V}")
            else:
                lines.append(f"{self.BORDER_V}".ljust(41) + f"{self.BORDER_V}")
             
        lines.append(f"{self.TEE_L}{self.BORDER_H * width}{self.TEE_R}")
        menu = " [C]reate   [J]oin   [R]efresh   [Q]uit "
        lines.append(f"{self.BORDER_V}{menu}".ljust(41) + f"{self.BORDER_V}")
        lines.append(f"{self.CORNER_BL}{self.BORDER_H * width}{self.CORNER_BR}")
        
        return lines