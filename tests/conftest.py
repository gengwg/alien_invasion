"""Shared test setup: headless SDL and isolated profile/high-score files.

Run the suite with:
    .venv/bin/python -m pytest tests/ -v
"""

import os

# Headless SDL must be configured before the game initializes pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import alien_invasion


@pytest.fixture(autouse=True)
def isolated_data_files(tmp_path, monkeypatch):
    """Never touch the developer's real profiles.json / high_score.txt."""
    monkeypatch.setattr(alien_invasion, "PROFILES_FILE",
                        str(tmp_path / "profiles.json"))
    monkeypatch.setattr(alien_invasion, "HIGH_SCORE_FILE",
                        str(tmp_path / "high_score.txt"))
    return tmp_path


@pytest.fixture
def game():
    """A fresh, headless game instance."""
    ai = alien_invasion.AlienInvasion()
    yield ai
    pygame.quit()
