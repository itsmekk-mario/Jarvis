from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from brain import JarvisBrain


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv()

app = FastAPI(title="Jarvis Web UI")
brain = JarvisBrain()


class AskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        return AskResponse(answer=brain.ask(request.text.strip()))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
