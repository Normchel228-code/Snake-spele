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
    app.name = "Guest"
    app.uploader = type("Uploader", (), {"started": False, "status": "", "failed": False})()
    app.new_round = lambda: setattr(app.game, "reset_called", True)

    app.handle_game_key(DummyEvent(pygame.K_r, scancode=None))

    assert getattr(app.game, "reset_called", False) is True


def test_pause_key_works_on_key_not_scancode():
    app = object.__new__(App)
    app.in_menu = False
    app.running = True
    app.game = Game(10, 10)
    app.name = "Guest"
    app.uploader = type("Uploader", (), {"started": False, "status": "", "failed": False})()
    app.new_round = lambda: None

    app.handle_game_key(DummyEvent(pygame.K_p, scancode=None))

    assert app.game.paused is True


def test_easy_difficulty_slows_everything_by_half():
    game = Game(10, 10)
    game.difficulty = "easy"

    assert game.config.step_time == 0.135 / 0.5
    assert game.config.zone_interval == 7.0 / 0.5
    assert game.config.dark_drain == 1.5 * 0.5


def test_hard_difficulty_speedups_everything_by_one_point_five():
    game = Game(10, 10)
    game.difficulty = "hard"

    assert game.config.step_time == 0.135 / 1.5
    assert game.config.zone_interval == 7.0 / 1.5
    assert game.config.dark_drain == 1.5 * 1.5


def test_number_keys_choose_difficulty_from_menu():
    app = object.__new__(App)
    app.in_menu = True
    app.name = ""
    app.difficulty = None
    app.game = Game(10, 10)

    app.handle_menu_key(DummyEvent(key=pygame.K_1, scancode=None))
    assert app.difficulty == "easy"

    app.handle_menu_key(DummyEvent(key=pygame.K_3, scancode=None))
    assert app.difficulty == "hard"


def test_enter_requires_selected_difficulty():
    app = object.__new__(App)
    app.in_menu = True
    app.name = ""
    app.difficulty = None
    app.game = Game(10, 10)
    app.uploader = type("Uploader", (), {"started": False, "status": "", "failed": False})()
    app.new_round = lambda: setattr(app, "round_started", True)

    app.handle_menu_key(DummyEvent(key=pygame.K_RETURN, scancode=None))

    assert getattr(app, "round_started", False) is False
    assert app.in_menu is True
