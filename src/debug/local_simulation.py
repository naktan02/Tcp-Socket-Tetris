# src/debug/local_simulation.py
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.game_state import GameState
from src.client.renderer import Renderer
from src.client.input_handler import InputHandler
from src.common.constants import Action

def main():
    game = GameState()
    renderer = Renderer() # 여기서 Alternate Screen Buffer 진입
    input_handler = InputHandler()
    
    # print 문 대신 renderer를 통해서만 출력해야 화면이 안 깨짐
    
    last_tick = time.time()
    
    try:
        while not game.game_over:
            action = input_handler.get_action()
            if action:
                if action == Action.QUIT:
                    break
                game.process_input(action)
            
            current_time = time.time()
            if current_time - last_tick > 0.5: 
                game.update()
                last_tick = current_time
                
            renderer.draw(game)
            time.sleep(0.01)
            
        renderer.draw(game)
        renderer.draw_game_over()
        time.sleep(2) # 게임 오버 메시지 2초간 보여줌
        
    except KeyboardInterrupt:
        pass
    finally:
        # 프로그램 종료 시 명시적으로 renderer 삭제 -> 터미널 복구 코드 실행
        del renderer
        print("Simulation End.")

if __name__ == "__main__":
    main()