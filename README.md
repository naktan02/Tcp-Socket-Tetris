제공해주신 코드와 파일 구조를 바탕으로 `README.md` 초안을 작성했습니다. 이 문서는 프로젝트 개요, 설치 및 실행 방법, 시스템 아키텍처, 프로토콜 명세 등을 포함하여 개발자나 사용자가 프로젝트를 쉽게 이해하고 실행할 수 있도록 구성되었습니다.

---

# TCP Socket Tetris

**TCP Socket Tetris**는 Python의 Raw Socket(`socket` 모듈)을 사용하여 구현한 멀티플레이어 콘솔 테트리스 게임입니다. 서버-클라이언트 아키텍처를 기반으로 하며, 커스텀 바이너리 프로토콜을 통해 실시간 게임 동기화와 방 관리 시스템(Lobby-Room)을 지원합니다.

---

## 📋 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [설치 및 실행 방법](#-설치-및-실행-방법)
3. [프로젝트 구조](#-프로젝트-구조)
4. [프로토콜 명세](#-프로토콜-명세-protocol-specification)
5. [주요 기능](#-주요-기능)
6. [설정 가이드](#-설정-가이드)

---

## 🚀 프로젝트 개요

* **언어**: Python 3.12+
* **통신 방식**: TCP/IP 소켓 (Blocking/Non-blocking 혼용 또는 Select/Thread 방식 사용 추정)
* **UI**: ANSI Escape Code를 활용한 터미널 기반 그래픽
* **아키텍처**: 중앙 집중형 서버 (Room Manager 관리)

---

## 💻 설치 및 실행 방법

### 사전 요구 사항

* Python 3.x 환경이 설치되어 있어야 합니다.
* 별도의 외부 라이브러리(`pip install`) 없이 표준 라이브러리만으로 동작합니다.

### 1. 서버 실행

서버는 `0.0.0.0:5000`에서 클라이언트의 연결을 대기합니다.

```bash
python main_server.py

```

> 서버가 시작되면 `[Main] Server Started` 메시지와 함께 대기 상태로 진입합니다.

### 2. 클라이언트 실행

새로운 터미널 창을 열어 클라이언트를 실행합니다. 멀티플레이 테스트를 위해 여러 개의 터미널에서 실행할 수 있습니다.

```bash
python main_client.py

```

> 실행 후 닉네임을 입력하고 로비에 접속하여 방을 생성하거나 기존 방에 입장할 수 있습니다.

---

## 📂 프로젝트 구조

```text
Tcp-Socket-Tetris/
├── main_server.py           # [Entry] 서버 실행 진입점
├── main_client.py           # [Entry] 클라이언트 실행 진입점
├── game_debug.log           # 게임 로그 파일
├── src/
│   ├── common/              # 공통 모듈 (프로토콜, 상수, 유틸리티)
│   │   ├── config.py        # 포트, 버퍼 크기 등 설정
│   │   ├── constants.py     # 패킷 CMD 코드, 키 입력 상수
│   │   └── protocol.py      # 패킷 직렬화/역직렬화 (Marshalling)
│   ├── server/              # 서버 사이드 로직
│   │   ├── infra/           # 소켓 연결, 라우팅 등 코어 로직
│   │   ├── handlers/        # 비즈니스 로직 처리 (로그인, 게임 등)
│   │   └── game/            # 방(Room) 및 게임 세션 관리
│   ├── client/              # 클라이언트 사이드 로직
│   │   ├── core/            # 렌더링 엔진, 입력 처리, 씬 매니저
│   │   ├── network/         # 서버 통신 및 패킷 처리
│   │   ├── scenes/          # 화면별 상태 관리 (Login, Lobby, InGame)
│   │   └── ui/              # 콘솔 UI 드로잉 모듈
│   └── core/                # 테트리스 게임 엔진 (순수 로직)
│       ├── board.py         # 게임 보드 상태 관리
│       ├── tetromino.py     # 테트리스 블록 정의
│       └── game_state.py    # 게임 진행 상태

```

---

## 📡 프로토콜 명세 (Protocol Specification)

네트워크 효율성을 위해 **고정 헤더(Fixed Header)**와 **가변 바디(Variable Body)** 구조를 가진 바이너리 프로토콜을 사용합니다.

### 패킷 구조 (Packet Structure)

`[LEN (2 bytes)]` + `[CMD (1 byte)]` + `[BODY (N bytes)]`

| 필드 | 크기 | 타입 | 설명 |
| --- | --- | --- | --- |
| **LEN** | 2 Bytes | `Unsigned Short` (Big-Endian) | 이후에 오는 데이터(`CMD` + `BODY`)의 총 길이 |
| **CMD** | 1 Byte | `Unsigned Char` | 요청/응답의 종류를 식별하는 커맨드 코드 |
| **BODY** | N Bytes | `Bytes` / `String` | 실제 데이터 페이로드 (JSON 문자열 또는 바이너리) |

### 주요 커맨드 (Command Codes)

자세한 코드는 `src/common/constants.py`를 참조하십시오.

* **연결 관리**: `REQ_LOGIN(0x01)`, `RES_LOGIN(0x02)`
* **방 관리**:
* `REQ_CREATE_ROOM(0x11)`, `RES_CREATE_ROOM(0x12)`
* `REQ_JOIN_ROOM(0x13)`, `RES_JOIN_ROOM(0x14)`
* `NOTI_ENTER_ROOM(0x15)`: 다른 유저 입장 알림


* **게임 플레이**:
* `NOTI_GAME_START(0x22)`: 게임 시작 (동기화 시드 포함)
* `REQ_MOVE(0x30)`, `NOTI_MOVE(0x31)`: 블록 이동 동기화
* `REQ_ATTACK(0x40)`, `NOTI_GARBAGE(0x41)`: 공격 및 방해 줄 생성



---

## ✨ 주요 기능

### 1. 방 관리 시스템 (Room Management)

* **RoomManager**가 방의 생성(Create), 조회(Search), 입장(Join), 퇴장(Leave)을 중앙에서 관리합니다.
* 최대 4명까지 하나의 방에 접속하여 경쟁할 수 있습니다. (`MAX_ROOM_SLOTS = 4`)

### 2. 공정한 게임 동기화

* 게임 시작 시 서버가 난수 시드(Seed)를 생성하여 모든 클라이언트에게 전송합니다 (`CMD_NOTI_GAME_START`).
* 이를 통해 모든 플레이어가 동일한 순서의 테트리스 블록을 받게 되어 공정한 경쟁이 가능합니다.

### 3. 콘솔 UI & 렌더링

* ANSI Escape Code를 사용하여 터미널 상에서 컬러풀한 블록과 UI를 렌더링합니다.
* 더블 버퍼링 혹은 커서 이동 방식을 통해 깜빡임을 최소화한 화면 갱신을 수행합니다.

### 4. 에러 핸들링

* 클라이언트 실행 중 예외 발생 시, `traceback`을 통해 에러 로그를 출력하고 사용자가 엔터를 누르기 전까지 창이 닫히지 않도록 안전 장치가 구현되어 있습니다.

---

## ⚙️ 설정 가이드

`src/common/config.py` 파일에서 주요 설정을 변경할 수 있습니다.

```python
HOST = '0.0.0.0'       # 서버 바인딩 주소
PORT = 5000            # 사용 포트
BUFFER_SIZE = 4096     # 소켓 수신 버퍼 크기
TICK_RATE = 30         # 초당 로직 갱신 횟수 (FPS)

```