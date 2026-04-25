# Jarvis 1.0

Jarvis 1.0은 macOS와 Windows에서 실행할 수 있는 로컬 AI 비서입니다. Ollama로 로컬 LLM을 실행하고, 사용자의 문장을 의도로 분류한 뒤 웹 검색, 날씨 조회, 파일 검색, 일정 관리, 웹페이지 요약, 앱 실행 같은 작업을 수행합니다.

CLI와 Web UI를 모두 제공합니다. Web UI는 중앙 코어 애니메이션과 텍스트 입력 인터페이스를 포함합니다.

## 주요 기능

- **로컬 LLM 연동**: Ollama API를 사용하며 기본 모델은 `gemma3:12b`입니다.
- **의도 분석**: 사용자 입력을 `search`, `weather`, `file_search`, `schedule` 등으로 분류합니다.
- **웹 검색**: DuckDuckGo HTML 검색 결과를 가져와 핵심 내용을 요약합니다.
- **URL 읽기**: 사용자가 입력한 URL의 본문을 가져와 한국어로 요약합니다.
- **날씨 조회**: `wttr.in`을 통해 현재 날씨와 당일 예보를 조회합니다.
- **로컬 파일 검색**: 파일명과 일부 텍스트 파일 내용을 검색합니다.
- **일정 관리**: SQLite 데이터베이스에 일정을 저장하고 조회합니다.
- **앱 실행**: macOS, Windows, Linux 환경에 맞는 방식으로 Chrome, Edge, 메모장/Notes, 탐색기/Finder 같은 앱을 실행합니다.
- **CLI/Web UI 지원**: 터미널 기반 실행과 FastAPI 기반 웹 인터페이스를 제공합니다.

## 프로젝트 구조

```text
Jarvis/
├── main.py                # CLI 진입점
├── web_app.py             # FastAPI Web UI 서버
├── brain.py               # Ollama 연동 및 의도 분석
├── actions.py             # 의도별 실제 작업 처리
├── memory.py              # SQLite 일정 저장소
├── browser_actions.py     # 브라우저 URL 열기 유틸
├── google_services.py     # Gmail/YouTube 연동 유틸
├── search.py              # Tavily 검색 유틸
├── voice.py               # 음성 입력 유틸
├── tts.py                 # TTS 출력 유틸
├── static/                # Web UI 정적 파일
├── requirements.txt       # 기본 의존성
└── requirements-voice.txt # 음성 기능용 추가 의존성
```

## 요구 사항

- macOS 또는 Windows 권장
- Python 3.9 이상
- Ollama
- 인터넷 연결
  - 웹 검색, 날씨 조회, URL 읽기, gTTS, Google API 기능에 필요합니다.

Ollama는 아래 페이지에서 설치할 수 있습니다.

https://ollama.com/

## 설치

1. 저장소를 내려받습니다.

   ```bash
   git clone https://github.com/itsmekk-mario/Jarvis.git
   cd Jarvis
   ```

2. 가상환경을 만들고 활성화합니다.

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Windows CMD:

   ```cmd
   py -3 -m venv .venv
   .venv\Scripts\activate.bat
   ```

3. 기본 의존성을 설치합니다.

   ```bash
   pip install -r requirements.txt
   ```

4. 사용할 Ollama 모델을 내려받습니다.

   ```bash
   ollama pull gemma3:12b
   ```

## 환경 변수 설정

Jarvis는 `Jarvis/.env` 파일을 자동으로 읽습니다. 파일이 없어도 기본값으로 실행되지만, 모델이나 검색 범위를 바꾸고 싶다면 직접 생성하세요.

```bash
touch .env
```

Windows PowerShell:

```powershell
New-Item -ItemType File .env
```

예시:

```env
OLLAMA_MODEL=gemma3:12b
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_TIMEOUT=240
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=768

JARVIS_DEFAULT_LOCATION=Seoul
JARVIS_FILE_SEARCH_ROOTS=~/Documents,~/Desktop
JARVIS_FILE_SEARCH_MAX_RESULTS=12
JARVIS_FILE_SEARCH_MAX_FILES=8000
```

Windows에서는 경로를 다음처럼 적을 수 있습니다.

```env
JARVIS_FILE_SEARCH_ROOTS=C:\Users\your-name\Documents,C:\Users\your-name\Desktop
```

### 주요 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OLLAMA_MODEL` | `gemma3:12b` | 사용할 Ollama 모델 이름 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API 주소 |
| `OLLAMA_TIMEOUT` | `240` | Ollama 요청 타임아웃 초 |
| `OLLAMA_NUM_CTX` | `2048` | 모델 컨텍스트 크기 |
| `OLLAMA_NUM_PREDICT` | `768` | 일반 응답 최대 생성 토큰 |
| `OLLAMA_THINK` | `false` | `true`로 설정하면 Ollama `think` 옵션을 켭니다 |
| `JARVIS_DEFAULT_LOCATION` | `Seoul` | 날씨 조회 기본 지역 |
| `JARVIS_FILE_SEARCH_ROOTS` | 홈 디렉터리 | 쉼표로 구분한 파일 검색 경로 |
| `JARVIS_FILE_SEARCH_MAX_RESULTS` | `12` | 파일 검색 최대 결과 수 |
| `JARVIS_FILE_SEARCH_MAX_FILES` | `8000` | 파일 검색 최대 스캔 파일 수 |

## 실행 방법

### 1. Ollama 서버 실행

다른 터미널에서 Ollama 서버를 먼저 실행합니다.

```bash
ollama serve
```

이미 Ollama 앱이 실행 중이라면 이 단계는 생략할 수 있습니다.

### 2. CLI 모드 실행

macOS/Linux:

```bash
python3 main.py
```

Windows:

```powershell
py main.py
```

종료하려면 `종료`, `exit`, `quit`, `q` 중 하나를 입력합니다.

### 3. Web UI 실행

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Windows에서 `uvicorn` 명령을 찾지 못하면 아래처럼 실행합니다.

```powershell
py -m uvicorn web_app:app --host 127.0.0.1 --port 8000
```

브라우저에서 아래 주소를 엽니다.

http://127.0.0.1:8000

상태 확인 API:

```bash
curl http://127.0.0.1:8000/api/health
```

명령 요청 API:

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"text":"서울 날씨 알려줘"}'
```

## 사용 예시

```text
서울 날씨 알려줘
나무위키에서 Python 찾아줘
https://example.com 이 페이지 요약해줘
내 컴퓨터에서 report 파일 찾아줘
내일 오후 3시 회의 일정 추가해줘
일정 조회해줘
크롬 열어줘
메모장 열어줘
파일 탐색기 열어줘
이 메시지에 답장 써줘: 오늘 회의 참석 가능하세요?
```

## 의도 분류

Jarvis는 사용자 입력을 다음 의도 중 하나로 분류합니다.

| Intent | 설명 |
| --- | --- |
| `search` | 웹 검색 |
| `weather` | 날씨 조회 |
| `file_search` | 로컬 파일 검색 |
| `browse_url` | URL 본문 읽기 및 요약 |
| `schedule` | 일정 추가/조회 |
| `reply` | 메일, 카톡, 메시지 답장 작성 |
| `summarize` | 긴 글 요약 |
| `open_app` | 데스크톱 앱 실행 |
| `quick_reply` | 짧은 인사 또는 즉시 응답 |
| `unknown` | 처리 도구가 없는 요청 |

## 모델 변경

다른 Ollama 모델을 쓰려면 먼저 모델을 내려받습니다.

```bash
ollama pull llama3.1
```

그다음 `.env`의 `OLLAMA_MODEL` 값을 바꿉니다.

```env
OLLAMA_MODEL=llama3.1
```

변경 후 CLI 또는 Web UI 서버를 재시작하면 새 모델이 적용됩니다.

## 일정 데이터

일정은 `Jarvis/jarvis.db` SQLite 파일에 저장됩니다. 이 파일은 실행 중 자동으로 생성됩니다.

현재 지원하는 일정 기능은 간단한 추가와 조회입니다.

```text
내일 오후 2시 병원 일정 추가해줘
일정 조회해줘
```

## 파일 검색 범위

기본 검색 범위는 사용자 홈 디렉터리입니다. 다만 `.git`, `.venv`, `node_modules`, `Library`, `Applications`, `AppData`, `Program Files`, `Windows`, `Pictures`, `Movies`, `Music` 등은 검색에서 제외됩니다.

검색 범위를 좁히려면 `.env`에 `JARVIS_FILE_SEARCH_ROOTS`를 설정하세요.

```env
JARVIS_FILE_SEARCH_ROOTS=~/Documents,~/Desktop
```

파일 내용 검색은 `.txt`, `.md`, `.csv`, `.json`, `.py`, `.js`, `.html`, `.css`, `.log` 파일을 대상으로 하며, 1MB 이하 파일만 읽습니다.

## 선택 기능

### 음성 입력

음성 기능을 사용하려면 추가 의존성을 설치합니다.

```bash
pip install -r requirements-voice.txt
```

`voice.py`는 기본적으로 `speech_recognition`을 사용합니다. Whisper를 쓰려면 환경 변수를 설정합니다.

```env
VOICE_INPUT_ENGINE=whisper
```

### TTS

`tts.py`는 기본적으로 `gtts`를 사용하고, `pyttsx3`도 선택할 수 있습니다.

```env
TTS_ENGINE=pyttsx3
```

### Google 서비스

`google_services.py`에는 Gmail과 YouTube 연동 유틸이 포함되어 있습니다. 사용하려면 Google OAuth 클라이언트 파일이 필요합니다.

```env
GOOGLE_CLIENT_SECRET_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
JARVIS_ALLOW_EMAIL_SEND=false
```

메일 실제 전송은 기본적으로 비활성화되어 있습니다. 실제 전송을 허용하려면 `JARVIS_ALLOW_EMAIL_SEND=true`를 설정해야 합니다.

## 문제 해결

### Ollama 서버에 연결할 수 없는 경우

```bash
ollama serve
```

를 실행했는지 확인하세요. Ollama 주소를 바꿨다면 `.env`의 `OLLAMA_BASE_URL`도 함께 수정해야 합니다.

### 모델을 찾을 수 없는 경우

```bash
ollama pull gemma3:12b
```

또는 `.env`에 설정한 모델명을 확인합니다.

### Windows에서 Ollama 500 오류가 나는 경우

먼저 Ollama가 정상 응답하는지 확인합니다.

```powershell
ollama list
ollama run gemma3:12b "안녕"
```

모델이 없으면 다시 내려받습니다.

```powershell
ollama pull gemma3:12b
```

Jarvis가 사용하는 API를 직접 확인하려면 PowerShell에서 실행합니다.

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:11434/api/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"model":"gemma3:12b","messages":[{"role":"user","content":"안녕"}],"stream":false}'
```

여기서도 500이 나면 Jarvis 문제가 아니라 Ollama 또는 모델 실행 문제입니다. Ollama를 재시작하거나 모델을 다시 pull하고, 그래도 안 되면 Ollama를 최신 버전으로 업데이트하세요.

### Web UI 실행 시 `fastapi` 또는 `uvicorn` 오류가 나는 경우

```bash
pip install -r requirements.txt
```

으로 기본 의존성을 다시 설치합니다.

### 날씨나 웹 검색이 실패하는 경우

인터넷 연결 상태를 확인하세요. 날씨는 `wttr.in`, 웹 검색은 DuckDuckGo HTML 페이지에 접근합니다.

### 앱 실행이 실패하는 경우

앱 이름이 현재 OS에 등록된 이름과 일치해야 합니다.

macOS 예시:

```text
사파리 열어줘
메모 열어줘
파인더 열어줘
```

Windows 예시:

```text
크롬 열어줘
엣지 열어줘
메모장 열어줘
파일 탐색기 열어줘
계산기 열어줘
```

## 라이선스

MIT
