# Jarvis AI Assistant

Mac에서 실행 가능한 한국어 음성 AI 비서 예제입니다.

## 기능

- Wake word: "자비스"
- 마이크 음성 입력: 기본 `speech_recognition`, 선택 `Whisper`
- 자연어 처리: OpenAI API function calling
- 웹 검색: Tavily API
- 음성 출력: 기본 `gTTS`, 선택 `pyttsx3`
- Google 계정 연동: Gmail 읽기/초안/선택적 전송, YouTube 검색/구독 목록
- 브라우저 자동 열기: YouTube 검색, Instagram 홈/공개 프로필, 일반 URL
- Web UI: 사이버 HUD 스타일의 회전 코어, 음성 응답 중 확대/축소 애니메이션

## 설치

```bash
cd ~/jarvis_assistant
python3 -m venv .venv
source .venv/bin/activate
brew install portaudio
pip install --upgrade pip
pip install -r requirements.txt
```

터미널 앱에서 직접 마이크 입력을 쓰는 `python main.py` 모드까지 설치하려면 `PyAudio`가 필요합니다.

```bash
brew install portaudio
pip install -r requirements-voice.txt
```

`PyAudio` 설치가 실패하면 아래처럼 include/library 경로를 명시합니다.

```bash
brew install portaudio
export CPPFLAGS="-I$(brew --prefix portaudio)/include"
export LDFLAGS="-L$(brew --prefix portaudio)/lib"
pip install PyAudio
```

## 환경 변수

```bash
cp .env.example .env
```

`.env` 파일에 API 키를 입력합니다.

```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
OPENAI_MODEL=gpt-4o-mini
VOICE_INPUT_ENGINE=speech_recognition
TTS_ENGINE=gtts
GOOGLE_CLIENT_SECRET_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
JARVIS_ALLOW_EMAIL_SEND=false
```

Whisper를 쓰려면:

```bash
VOICE_INPUT_ENGINE=whisper
```

오프라인 TTS를 쓰려면:

```bash
TTS_ENGINE=pyttsx3
```

## Google 계정 연동

Google 계정 접근은 비밀번호가 아니라 OAuth 승인으로 처리합니다.

1. Google Cloud Console에서 프로젝트를 만듭니다.
2. Gmail API와 YouTube Data API v3를 활성화합니다.
3. OAuth 동의 화면을 설정합니다.
4. 데스크톱 앱 유형의 OAuth Client를 생성합니다.
5. 내려받은 JSON 파일을 `~/jarvis_assistant/credentials.json`으로 저장합니다.

처음 Gmail 또는 YouTube 명령을 실행하면 브라우저가 열리고 Google 로그인/권한 승인 화면이 표시됩니다. 승인 후 `token.json`이 생성되어 다음 실행부터 재사용됩니다.

기본적으로 실제 메일 전송은 막혀 있습니다. 정말 음성 명령으로 전송까지 허용하려면 `.env`에서 아래처럼 바꿉니다.

```bash
JARVIS_ALLOW_EMAIL_SEND=true
```

권장 사용은 "메일 초안 만들어줘"입니다.

## 실행

```bash
cd ~/jarvis_assistant
source .venv/bin/activate
python main.py
```

실행 후 "자비스"라고 부른 다음 명령을 말하세요.

## Web UI 실행

```bash
cd ~/jarvis_assistant
source .venv/bin/activate
uvicorn web_app:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:8000
```

Web UI에서는 중앙 코어가 계속 회전하고, Jarvis가 말하는 동안 코어가 커졌다 작아집니다. 브라우저가 음성 인식을 지원하면 "자비스" wake word를 듣고, 중앙 코어를 눌러 명령 대기 상태로 전환할 수도 있습니다.

예:

- "자비스"
- "오늘 OpenAI 최신 뉴스 요약해줘"
- "애플 주가 관련 최신 소식 알려줘"
- "최근 안 읽은 메일 요약해줘"
- "홍길동에게 회의 일정 확인 메일 초안 만들어줘"
- "내 유튜브 구독 채널 몇 개 읽어줘"
- "유튜브에서 Python 강의 검색해서 열어줘"
- "인스타그램 열어줘"
- "인스타그램 openai 프로필 열어줘"
- "종료"

## 제한 사항

- Instagram은 공식 개인 계정 자동화 API가 제한적입니다. 이 예제는 로그인 우회, 비공개 정보 수집, 자동 좋아요/팔로우/DM 발송을 하지 않고 브라우저에서 홈 또는 공개 프로필을 여는 수준으로 동작합니다.
- Gmail 실제 전송은 실수 방지를 위해 환경 변수로 별도 허용해야 합니다.
