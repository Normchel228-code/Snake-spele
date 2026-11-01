"""FastAPI serveris: rezultātu REST API un HTML lapas."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from api import db

BASE_DIR = Path(__file__).parent
MAX_NAME_LENGTH = 12  # Jāsakrīt ar MAX_NAME klientā.
MAX_SCORE = 1_000_000
NAME_PATTERN = r"^[\w-]+$"  # Burti, cipari, _ un -.


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Servera starta laikā izveido datubāzi."""
    db.init_db()
    yield


app = FastAPI(title="Snake: Light & Dark API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"),
          name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class ScoreIn(BaseModel):
    """Ienākošais rezultāts (validē Pydantic)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH,
                      pattern=NAME_PATTERN)
    score: int = Field(strict=True, ge=0, le=MAX_SCORE)


class ScoreOut(ScoreIn):
    """Saglabātais rezultāts ar id."""

    id: int


class ScoreRow(BaseModel):
    """Rinda līderu tabulā."""

    name: str
    score: int
    created_at: str


class PlayerStats(BaseModel):
    """Spēlētāja statistika."""

    name: str
    games: int
    best: int
    average: float
    last_played: str


# ---------- REST API ----------

@app.post("/scores", response_model=ScoreOut, status_code=201)
def create_score(payload: ScoreIn) -> dict:
    """Saglabā rezultātu. 201 — izveidots jauns ieraksts."""
    score_id = db.add_score(payload.name, payload.score)
    return {"id": score_id, **payload.model_dump()}


@app.get("/scores/top", response_model=list[ScoreRow])
def get_top_scores() -> list[dict]:
    """Top-10 rezultāti."""
    return db.top_scores(10)


@app.get("/players/{name}/stats", response_model=PlayerStats)
def get_player_stats(name: str) -> dict:
    """Spēlētāja statistika; 404, ja spēlētāja nav."""
    stats = db.player_stats(name)
    if stats is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return stats


# ---------- HTML lapas ----------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def leaderboard_page(request: Request) -> HTMLResponse:
    """Līderu tabula (top-10)."""
    return templates.TemplateResponse(
        request, "index.html", {"rows": db.top_scores(10)}
    )


@app.get("/players/{name}", response_class=HTMLResponse,
         include_in_schema=False)
def player_page(request: Request, name: str) -> HTMLResponse:
    """Spēlētāja profils ar statistiku."""
    stats = db.player_stats(name)
    status = 200 if stats else 404
    return templates.TemplateResponse(
        request, "player.html", {"name": name, "stats": stats},
        status_code=status,
    )


@app.get("/rules", response_class=HTMLResponse, include_in_schema=False)
def rules_page(request: Request) -> HTMLResponse:
    """Spēles apraksts un noteikumi."""
    return templates.TemplateResponse(request, "rules.html", {})
