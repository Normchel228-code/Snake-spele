"""SQLite datubāze: rezultātu tabula un vaicājumi."""

import os  # piekļuve vides mainīgajiem, piemēram SNAKE_DB
import sqlite3  # SQLite API: connect, execute, commit/rollback
from collections.abc import Generator  # ģeneratora tips, ko atgriež `@contextmanager`
from contextlib import contextmanager  # padara funkciju par `with ... as ...` menedžeri
from pathlib import Path  # darba ar faila ceļiem, lai atrastu DB failu

DEFAULT_DB = Path(__file__).with_name("scores.db")


def db_path() -> Path:
    """Datubāzes fails (var nomainīt ar vides mainīgo SNAKE_DB)."""
    return Path(os.environ.get("SNAKE_DB", DEFAULT_DB))


# `with connect() as conn:` automātiski atver un aizver savienojumu.
@contextmanager
def connect() -> Generator[sqlite3.Connection, None, None]:
    # `None, None` => ģenerators neņem nevienu vērtību (send) un negriež rezultātu; tas tikai "atdod" `conn` uz `with ... as conn`.
    """Atver savienojumu; veiksmē saglabā izmaiņas, kļūdā atceļ."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn  # nodod savienojumu uz `as conn` blokā; pēc bloka darbosies `finally`
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
    # `limit` ir skaitlis, `list[dict]` nozīmē atgriežam sarakstu ar vārdnīcām.
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
    # `name` ir teksts; atgriežam vārdnīcu ar statistiku vai `None`, ja spēlētājs nav atrasts.
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
# `**dict(row)` = "atver vārdnīcu": paņem visas atslēgas un vērtības no `row`
# un ievieto tās jaunā vārdnīcā. Tādējādi `name` pievienojam pats,
# bet pārējie lauki (`games`, `best`, `average`, `last_played`) nāk no SQL-atbildes.
    return {"name": name, **dict(row)}
