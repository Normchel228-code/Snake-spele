import sys
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client.main import App
from game.logic import Game


class DummyEvent:
    def __init__(self, key: int, scancode: int | None = None):
        self.key = key
        self.scancode = scancode


def test_restart_key_works_on_key_not_scancode():
    app = object.__new__(App)
    app.in_menu = False
    app.running = True
    app.game = Game(10, 10)
    app.name = "Alice"
    app.uploader = type("Uploader", (), {"started": False, "status": "", "failed": False})()
    app.new_round = lambda: setattr(app.game, "reset_called", True)

    app.handle_game_key(DummyEvent(pygame.K_r, scancode=None))

    assert getattr(app.game, "reset_called", False) is True


def test_pause_key_works_on_key_not_scancode():
    app = object.__new__(App)
    app.in_menu = False
    app.running = True
    app.game = Game(10, 10)
    app.name = "Alice"
    app.uploader = type("Uploader", (), {"started": False, "status": "", "failed": False})()
    app.new_round = lambda: None

    app.handle_game_key(DummyEvent(pygame.K_p, scancode=None))

    assert app.game.paused is True
