# main_client.py
import sys
import os
import traceback  # 자세한 에러 확인을 위해 추가

# src 모듈 경로 인식
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.client.scene_manager import SceneManager

def main():
    try:
        app = SceneManager()
        app.run()
    except KeyboardInterrupt:
        print("\nForce Quit.")
    except Exception:
        # 에러 발생 시 상세 내용을 출력하고 멈춤
        print("\n" + "="*60)
        print("!!! CRITICAL ERROR OCCURRED !!!")
        print("="*60)
        traceback.print_exc()  # 에러 위치 추적 출력
        print("="*60)
        print("\nPress Enter to exit...")
        input() # 엔터를 칠 때까지 꺼지지 않음
    finally:
        pass

if __name__ == "__main__":
    main()