"""FastAPI serveris: rezultātu REST API."""

from collections.abc import AsyncGenerator  # tips anotācijai: lifespan ir asinhrons ģenerators, kas dod `None` uz `async with`
from contextlib import asynccontextmanager  # dekorators: pārveido lifespan par objektu `async with` (FastAPI izsauc to startā un beigās)

from fastapi import FastAPI, HTTPException # fast api pēc nosacījumiem; HTTPException: kļūda ar HTTP kodu (piem., 404)
from pydantic import BaseModel, ConfigDict, Field  # BaseModel: datu modelis; ConfigDict: modeļa iestatījumi; Field: lauku ierobežojumi
from api import db

MAX_NAME_LENGTH = 12  # Jāsakrīt ar MAX_NAME klientā.
MAX_SCORE = 1_000_000
NAME_PATTERN = r"^[\w-]+$"  # Burti, cipari, _ un -.


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Servera starta laikā izveido datubāzi."""
    db.init_db()
    yield # apstājas šeit: serveris strādā; pēc izslēgšanas kods turpinās pēc yield (šeit nav nekā)


app = FastAPI(title="Snake: Light & Dark API", lifespan=lifespan)


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