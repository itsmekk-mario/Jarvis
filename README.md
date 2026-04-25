# Jarvis 1.0

Jarvis 1.0 is a local AI assistant for macOS. It uses Ollama, analyzes user intent, executes local actions, and features a cyber/dreamlike web UI with a dotted 3D animated core.

## Features

- **Local LLM via Ollama**: Default model `qwen3:4b`.
- **Enhanced Intent Analysis**: JSON-based classification.
- **Web Search & Browsing**: DuckDuckGo search and direct URL reading/summarization.
- **Local File Search**: Fast search for files and content on your machine.
- **Weather Information**: Real-time weather updates via wttr.in.
- **Schedule Management**: SQLite-backed personal schedule tracking.
- **System Control**: macOS app launcher.
- **Multi-Interface**: CLI and Interactive Web UI.

## Requirements

- **macOS** (Optimized for Mac, though many features work on Linux/Windows).
- **Python 3.9+**
- **Ollama**: [Download from ollama.com](https://ollama.com/)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/itsmekk-mario/Jarvis.git
   cd Jarvis
   ```

2. **Set up virtual environment & dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Copy the example environment file and customize it.
   ```bash
   cp .env.example .env
   ```

## How to Run Jarvis

### 1. Start Ollama
Ensure the Ollama server is running.
```bash
ollama serve
```

### 2. Run CLI Mode
For a simple terminal-based interaction:
```bash
python main.py
```

### 3. Run Web UI (Recommended)
Jarvis features a sophisticated web interface with voice support.
```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```
Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## How to Change the Model

Jarvis allows you to easily switch between different local models using the `.env` file.

1. **Pull the desired model via Ollama:**
   ```bash
   ollama pull llama3
   ```

2. **Edit your `.env` file:**
   Open `.env` and update the `OLLAMA_MODEL` variable:
   ```env
   # .env file
   OLLAMA_MODEL=llama3
   ```

3. **Restart Jarvis:**
   The next time you run `main.py` or the Web UI, Jarvis will use the new model.

---

## Intent Schema

Jarvis classifies input into the following intents:
- `search`: Web search (DuckDuckGo).
- `weather`: Weather information.
- `file_search`: Local file/content search.
- `browse_url`: Reading and summarizing a specific URL.
- `schedule`: Schedule management (Add/View).
- `reply`: Drafting replies for emails or messages.
- `summarize`: Summarizing long texts.
- `open_app`: Launching macOS applications.
- `quick_reply`: Immediate greetings or short responses.

## License

MIT
