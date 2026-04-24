# Local Jarvis with Ollama

MacOS에서 Ollama `qwen3:4b` 모델로 실행하는 로컬 AI 비서입니다. OpenAI API를 사용하지 않습니다.

## 파일 구조

```text
jarvis_assistant/
├── main.py
├── brain.py
├── actions.py
├── memory.py
├── utils.py
└── requirements.txt
```

## 기능

- Ollama API로 `qwen3:4b` 호출
- 사용자 입력을 JSON intent로 분석
- 웹 검색: DuckDuckGo HTML 검색
- 일정 관리: SQLite 저장/조회
- 답장 생성
- 긴 텍스트 요약
- Mac 앱 실행

Intent 형식:

```json
{
  "intent": "search | schedule | reply | summarize | open_app | unknown",
  "content": "사용자 요청 내용"
}
```

## 설치

Ollama가 설치되어 있고 서버가 실행 중이어야 합니다.

```bash
ollama pull qwen3:4b
```

프로젝트 의존성 설치:

```bash
cd ~/jarvis_assistant
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 실행

터미널 1:

```bash
ollama serve
```

이미 `address already in use`가 나오면 Ollama가 이미 실행 중인 것이므로 다음 단계로 넘어가면 됩니다.

터미널 2:

```bash
cd ~/jarvis_assistant
source .venv/bin/activate
python main.py
```

## 사용 예시

```text
오늘 애플 관련 최신 뉴스 검색해줘
나무위키에서 아이언맨 정보 찾아서 요약해줘
유튜브에서 맥북 에어 ollama 검색해줘
내일 오후 3시 병원 일정 추가해줘
일정 조회해줘
이 메시지에 답장 써줘: 오늘 회의 참석 가능하세요?
다음 글 요약해줘: ...
사파리 열어줘
크롬 실행해
```

## 참고

- 웹 검색은 DuckDuckGo HTML 페이지를 `requests`와 `BeautifulSoup`으로 읽습니다.
- 일정은 `jarvis.db` SQLite 파일에 저장됩니다.
- 앱 실행은 Mac의 `open -a 앱이름`을 사용합니다.
- OpenAI API 키는 필요하지 않습니다.
