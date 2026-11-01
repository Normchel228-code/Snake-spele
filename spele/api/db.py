"""SQLite datubāze: rezultātu tabula un vaicājumi."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).with_name("scores.db")


def db_path() -> Path:
    """Datubāzes fails (var nomainīt ar vides mainīgo SNAKE_DB)."""
    return Path(os.environ.get("SNAKE_DB", DEFAULT_DB))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Atver savienojumu; veiksmē saglabā izmaiņas, kļūdā atceļ."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Izveido tabulu, ja tās vēl nav."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL CHECK (score >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_scores_name ON scores (name)"
        )


def add_score(name: str, score: int) -> int:
    """Ieraksta rezultātu un atgriež tā id."""
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO scores (name, score) VALUES (?, ?)", (name, score)
        )
        return int(cursor.lastrowid)


def top_scores(limit: int = 10) -> list[dict]:
    """Labākie rezultāti: vispirms lielākie, pie vienādiem — vecākie."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT name, score, created_at FROM scores
            ORDER BY score DESC, created_at ASC, id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def player_stats(name: str) -> dict | None:
    """Spēlētāja statistika vai None, ja tādu spēlētāju nav."""
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS games,
                   MAX(score) AS best,
                   ROUND(AVG(score), 1) AS average,
                   MAX(created_at) AS last_played
            FROM scores WHERE name = ?
            """,
            (name,),
        ).fetchone()
    if row["games"] == 0:
        return None
    return {"name": name, **dict(row)}
