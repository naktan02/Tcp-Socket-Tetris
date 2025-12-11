# src/client/ui/console.py
import sys
import os

class Console:
    """터미널 제어 및 저수준 입출력 관리"""
    
    @staticmethod
    def init():
        """터미널 초기화 (Alternate Buffer 진입)"""
        sys.stdout.write("\033[?1049h")
        Console.hide_cursor()
        Console.clear()

    @staticmethod
    def cleanup():
        """터미널 복구 (Main Buffer 복귀)"""
        sys.stdout.write("\033[?1049l")
        Console.show_cursor()

    @staticmethod
    def hide_cursor():
        sys.stdout.write("\033[?25l")

    @staticmethod
    def show_cursor():
        sys.stdout.write("\033[?25h")

    @staticmethod
    def move_cursor(x, y):
        """커서를 (x, y)로 이동"""
        sys.stdout.write(f"\033[{y};{x}H")

    @staticmethod
    def home():
        """커서를 (0,0)으로 이동"""
        sys.stdout.write("\033[H")

    @staticmethod
    def clear():
        """화면 전체 지우기"""
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
            
    @staticmethod
    def print_lines(lines):
        """문자열 리스트를 한 번에 출력"""
        sys.stdout.write("\n".join(lines))
        sys.stdout.flush()

    @staticmethod
    def clear_line(y):
        """특정 줄을 공백으로 지움"""
        Console.move_cursor(1, y)
        sys.stdout.write(" " * 80)
        sys.stdout.flush()
        Console.move_cursor(1, y)