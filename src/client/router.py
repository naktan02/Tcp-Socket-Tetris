# src/client/router.py

def route(cmd_id):
    """
    핸들러 메서드에 CMD ID를 태깅하는 데코레이터
    (서버처럼 전역 등록이 아니라, 메서드 속성에 cmd_id를 저장함)
    """
    def decorator(func):
        # 함수 자체에 _cmd_id라는 속성을 심어둡니다.
        func._cmd_id = cmd_id
        return func
    return decorator