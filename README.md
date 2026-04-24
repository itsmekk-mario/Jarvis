# Jarvis 1.0

Jarvis 1.0 is a local AI assistant for macOS. It uses Ollama instead of the OpenAI API, analyzes user intent as JSON, executes local actions, and includes a cyber/dreamlike web UI with a dotted 3D animated core.

## Features

- Local LLM via Ollama
- Default model: `qwen3:4b`
- No OpenAI API required
- Korean-first responses
- JSON intent analysis
- DuckDuckGo web search
- SQLite schedule storage
- Reply drafting
- Long text summarization
- macOS app launcher
- CLI interface
- Web UI at `http://127.0.0.1:8000`

Intent schema:

```json
{
  "intent": "search | schedule | reply | summarize | open_app | unknown",
  "content": "사용자 요청 내용"
}
```

## Project Structure

```text
jarvis_assistant/
├── main.py
├── brain.py
├── actions.py
├── memory.py
├── utils.py
├── web_app.py
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── requirements.txt
```

## Requirements

- macOS
- Python 3.9+
- Ollama
- `qwen3:4b` or another local Ollama model

Install Python dependencies:

```bash
cd ~/jarvis_assistant
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Install the Ollama model:

```bash
ollama pull qwen3:4b
```

## Run CLI

Terminal 1:

```bash
ollama serve
```

If you see `address already in use`, Ollama is already running.

Terminal 2:

```bash
cd ~/jarvis_assistant
source .venv/bin/activate
python main.py
```

## Run Web UI

```bash
cd ~/jarvis_assistant
source .venv/bin/activate
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

The UI can render without Ollama, but command execution requires the Ollama server and model.

## Examples

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

## Notes

- Web search uses DuckDuckGo HTML results through `requests` and `BeautifulSoup`.
- Schedules are stored in `jarvis.db`.
- App launching uses macOS `open -a`.
- Generated local files such as `.env`, `.venv`, `jarvis.db`, and Ollama models are not committed.

## License

MIT
