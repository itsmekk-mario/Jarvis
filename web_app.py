from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from actions import JarvisActions
from brain import JarvisBrain
from memory import ScheduleMemory


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Jarvis Web UI")
brain = JarvisBrain()
actions = JarvisActions(brain=brain, memory=ScheduleMemory())


class AskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    intent: str


class HealthResponse(BaseModel):
    ollama_base_url: str
    ollama_model: str
    web_ui: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ollama_base_url=brain.base_url,
        ollama_model=brain.model,
        web_ui="ok",
    )


@app.get("/api/ask")
def ask_get_hint() -> dict[str, str]:
    return {
        "message": "이 주소는 POST 전용입니다. 브라우저에서는 http://127.0.0.1:8000/ 을 열어주세요.",
        "example": 'curl -X POST http://127.0.0.1:8000/api/ask -H "Content-Type: application/json" -d \'{"text":"일정 조회해줘"}\'',
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        intent = brain.analyze_intent(request.text.strip())
        result = actions.run(intent.intent, intent.content)
        if result.title == "일반 응답":
            answer = result.content
        else:
            answer = f"[{result.title}]\n{result.content}"
        return AskResponse(answer=answer, intent=intent.intent)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
