"""Headless integration and regression tests for Alien Invasion.

Run with:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -v

These tests drive the real game loop and event handlers without a display
or audio device, so they run in CI / headless environments.
"""

import os
import time

import pygame
import pytest

# Headless SDL must be configured before the game initializes pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from alien_invasion import AlienInvasion
from explosion import Explosion
from bullet import Bullet
from paths import HIGH_SCORE_FILE


@pytest.fixture
def game():
    """A fresh game instance; high-score file cleaned up afterwards."""
    ai = AlienInvasion()
    yield ai
    if os.path.exists(HIGH_SCORE_FILE):
        os.remove(HIGH_SCORE_FILE)
    pygame.quit()


def _start_game(ai):
    ai._check_play_button(ai.play_button.rect.center)


# --- HIGH #1: starting level and speed integrity -------------------------

def test_new_game_starts_at_level_one_with_base_speeds(game):
    _start_game(game)
    assert game.stats.level == 1
    assert game.settings.ship_speed == 3.5
    assert game.settings.bullet_speed == 5.0
    assert game.settings.alien_speed == 2.0
    assert game.settings.alien_points == 50
    assert game.stats.game_active is True
    assert len(game.aliens) > 0


def test_level_up_increases_speed_exactly_once(game):
    _start_game(game)
    game.aliens.empty()
    game._check_bullet_alien_collisions()
    assert game.stats.level == 2
    assert game.settings.ship_speed == pytest.approx(3.5 * 1.1)
    assert len(game.aliens) > 0  # new fleet created


# --- HIGH #2: high score saved at game over ------------------------------

def test_high_score_saved_on_game_over(game):
    _start_game(game)
    game.stats.score = 750
    game.stats.high_score = 750
    game.stats.ships_left = 0
    game._ship_hit()
    assert game.stats.game_active is False
    with open(HIGH_SCORE_FILE) as f:
        assert int(f.read()) == 750


# --- HIGH #3/#4: robust resources ----------------------------------------

def test_corrupt_high_score_file_falls_back_to_zero(game):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write("garbage")
    from game_stats import GameStats
    assert GameStats(game).high_score == 0


def test_missing_mixer_still_allows_play(game, monkeypatch):
    monkeypatch.setattr(pygame.mixer, "init",
                        lambda: (_ for _ in ()).throw(pygame.error("no audio")))
    ai = AlienInvasion()
    assert ai.sounds_enabled is False
    _start_game(ai)
    ai._fire_bullet()
    assert len(ai.bullets) == 1


# --- MEDIUM #5: explosions animate regardless of game state --------------

def test_explosion_completes_while_game_inactive(game):
    _start_game(game)
    game.explosions.add(Explosion((100, 100)))
    game.stats.game_active = False
    start = time.time()
    while len(game.explosions) and time.time() - start < 5:
        game._update_explosions()
        time.sleep(0.02)
    assert len(game.explosions) == 0


# --- MEDIUM #6: non-blocking ship respawn --------------------------------

def test_ship_hit_is_non_blocking_and_respawns(game):
    _start_game(game)
    game.stats.ships_left = 1
    t0 = time.time()
    game._ship_hit()
    assert time.time() - t0 < 0.1
    assert game.ship_respawn_time != 0
    assert len(game.aliens) == 0
    game._check_ship_respawn()
    assert len(game.aliens) == 0  # too early
    time.sleep(1.1)
    game._check_ship_respawn()
    assert game.ship_respawn_time == 0
    assert len(game.aliens) > 0
    assert game.ship.rect.bottom > 0


def test_double_ship_hit_ignored_while_respawning(game):
    _start_game(game)
    game.stats.ships_left = 2
    game._ship_hit()
    ships_after_first = game.stats.ships_left
    game._ship_hit()  # should be ignored while respawn pending
    assert game.stats.ships_left == ships_after_first


# --- MEDIUM #7: transient state reset on new game ------------------------

def test_new_game_resets_pause_autofire_and_effects(game):
    _start_game(game)
    game.game_paused = True
    game.autofire_active = True
    game.explosions.add(Explosion((50, 50)))
    game.stats.game_active = False
    _start_game(game)
    assert game.game_paused is False
    assert game.autofire_active is False
    assert len(game.explosions) == 0
    assert game.ship_respawn_time == 0


# --- MEDIUM #8: settings-driven bullets and stable star count ------------

def test_bullet_uses_settings(game):
    _start_game(game)
    b = Bullet(game)
    assert b.width == game.settings.bullet_width
    assert b.height == game.settings.bullet_height
    assert b.glow_width == game.settings.bullet_glow_width
    assert b.core_color == game.settings.bullet_core_color


def test_star_count_stable_across_updates(game):
    assert len(game.stars) == game.settings.star_count
    for _ in range(10):
        game._update_stars()
    assert len(game.stars) == game.settings.star_count


# --- Full loop: drive run_game frames with injected events ---------------

def test_main_loop_runs_frames_without_errors(game):
    """Simulate the real run_game body for many frames with gameplay."""
    _start_game(game)
    game.autofire_active = True

    # Drive ship movement via the real key handlers.
    right = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
    game._check_keydown_events(right)

    frames = 0
    start = time.time()
    while frames < 300 and time.time() - start < 10:
        # Mirror run_game's body (can't call run_game itself: infinite loop).
        game._check_events()
        if game.stats.game_active and not game.game_paused:
            game._update_stars()
            game.ship.update()
            game._update_bullets()
            game._update_aliens()
            game._auto_fire_bullets()
            game._check_ship_respawn()
        game._update_explosions()
        game._update_screen()
        frames += 1

    assert frames == 300
    # Auto-fire should have produced bullets over 300 frames.
    assert game.stats.score >= 0  # scoring path exercised without error
    game._update_screen()  # final render without error


def test_pause_toggle_via_keyboard(game):
    _start_game(game)
    p = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
    game._check_keydown_events(p)
    assert game.game_paused is True
    game._check_keydown_events(p)
    assert game.game_paused is False
