"""Headless integration and regression tests for Alien Invasion.

Run with:
    .venv/bin/python -m pytest tests/ -v

These tests drive the real game loop and event handlers without a display
or audio device, so they run in CI / headless environments. Shared setup
(headless SDL, isolated data files, the `game` fixture) lives in conftest.py.
"""

import time

import pygame
import pytest

from alien_invasion import AlienInvasion
from explosion import Explosion
from bullet import Bullet
from helpers import start_game as _start_game


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
    player = game.profiles.active
    game.stats.score = 750
    game.stats.high_score = 750
    game.stats.ships_left = 0
    game._ship_hit()
    assert game.stats.game_active is False
    assert game.profiles.stats_for(player)["high_score"] == 750


# --- HIGH #3/#4: robust resources ----------------------------------------

def test_high_score_comes_from_active_profile(game):
    from game_stats import GameStats
    game.profiles.create("Ace")
    game.profiles.record_game(score=640, level=3)
    assert GameStats(game).high_score == 640


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


def test_ship_hit_does_not_double_fleet_or_level(game):
    """Regression test: a ship hit must not be mistaken for a cleared fleet.

    _ship_hit empties the aliens group and defers recreation to the respawn
    timer. If _update_bullets runs during that window it sees an empty group;
    it must NOT treat that as "fleet destroyed" (which would spawn one fleet
    immediately and bump the level, then the respawn would stack a second
    fleet on top -- the doubling bug).
    """
    _start_game(game)
    initial_count = len(game.aliens)
    initial_level = game.stats.level
    game.stats.ships_left = 2

    game._ship_hit()
    assert len(game.aliens) == 0

    # Next frame: bullets update runs while the respawn is still pending.
    game._update_bullets()
    assert len(game.aliens) == 0, "fleet spawned early during respawn window"
    assert game.stats.level == initial_level, "level bumped by a ship hit"

    # After the delay, the respawn creates exactly one fleet.
    time.sleep(1.1)
    game._check_ship_respawn()
    assert len(game.aliens) == initial_count, (
        f"fleet doubled: {len(game.aliens)} vs {initial_count}")
    assert game.stats.level == initial_level


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


def test_star_recycles_to_top_when_off_screen(game):
    star = game.stars.sprites()[0]
    star.rect.y = game.settings.screen_height + 10
    game._update_stars()
    assert star.rect.top <= 0


# --- Full loop: drive run_game frames with injected events ---------------

def test_main_loop_runs_frames_without_errors(game):
    """Drive the real per-frame body of run_game with gameplay going on."""
    _start_game(game)
    game.autofire_active = True

    # Drive ship movement via the real key handlers.
    right = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
    game._check_keydown_events(right)

    frames = 0
    start = time.time()
    while frames < 120 and time.time() - start < 20:
        game._run_one_frame()  # what run_game's infinite loop calls
        frames += 1

    assert frames == 120
    assert game.stats.score >= 0  # scoring path exercised without error
    game._update_screen()  # final render without error


def test_frame_rate_is_capped(game):
    """The clock keeps a fast machine from running the game at warp speed."""
    assert game.settings.fps == 60
    _start_game(game)
    game._run_one_frame()  # first tick sets the clock's baseline

    frames = 30
    start = time.time()
    for _ in range(frames):
        game._run_one_frame()
    elapsed = time.time() - start

    # 30 frames at 60 fps take ~0.5s; allow generous slack for slow machines.
    assert elapsed > 0.5 * frames / game.settings.fps
    assert game.clock.get_fps() <= game.settings.fps * 1.5


def test_bullet_alien_collision_scores_and_explodes(game):
    _start_game(game)
    alien = game.aliens.sprites()[0]
    bullet = Bullet(game)
    bullet.rect.center = alien.rect.center
    game.bullets.add(bullet)

    aliens_before = len(game.aliens)
    game._check_bullet_alien_collisions()

    assert len(game.aliens) == aliens_before - 1
    assert game.stats.score == game.settings.alien_points
    assert game.stats.high_score == game.stats.score
    assert len(game.explosions) == 1
    assert len(game.bullets) == 0


def test_bullets_are_removed_at_top_of_screen(game):
    _start_game(game)
    game.aliens.empty()
    game.bullets.empty()
    bullet = Bullet(game)
    bullet.y = -bullet.rect.height  # already off the top of the screen
    game.bullets.add(bullet)
    game._update_bullets()
    assert len(game.bullets) == 0


def test_alien_touching_ship_costs_a_ship(game):
    _start_game(game)
    ships_before = game.stats.ships_left
    alien = game.aliens.sprites()[0]
    # Alien.update rewrites rect.x from alien.x, so move both.
    alien.x = float(game.ship.rect.centerx)
    alien.rect.x = game.ship.rect.centerx
    alien.rect.y = game.ship.rect.y
    game._update_aliens()
    assert game.stats.ships_left == ships_before - 1


def test_check_events_dispatches_key_events(game):
    _start_game(game)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT,
                                         unicode=""))
    game._check_events()
    assert game.ship.moving_right is True
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    game._check_events()
    assert game.ship.moving_right is False


def test_alien_reaching_bottom_costs_a_ship(game):
    _start_game(game)
    ships_before = game.stats.ships_left
    game.aliens.sprites()[0].rect.bottom = game.screen.get_rect().bottom
    game._check_aliens_bottom()
    assert game.stats.ships_left == ships_before - 1


def test_key_release_stops_movement_and_autofire(game):
    _start_game(game)
    for key in (pygame.K_RIGHT, pygame.K_LEFT, pygame.K_SPACE):
        game._check_keydown_events(pygame.event.Event(pygame.KEYDOWN, key=key))
    assert game.ship.moving_right and game.ship.moving_left
    game.ship.update()  # exercises both movement branches
    for key in (pygame.K_RIGHT, pygame.K_LEFT, pygame.K_SPACE):
        game._check_keyup_events(pygame.event.Event(pygame.KEYUP, key=key))
    assert not game.ship.moving_right and not game.ship.moving_left
    assert game.autofire_active is False


def test_enter_starts_game_when_idle(game):
    game._check_keydown_events(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
    assert game.stats.game_active is True


def test_quit_event_exits(game):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        game._check_events()


def test_mouse_click_is_handled(game):
    pygame.event.post(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)))
    game._check_events()  # off-button click: no crash, game stays idle
    assert game.stats.game_active is False


def test_explosions_are_drawn(game):
    _start_game(game)
    game.explosions.add(Explosion((100, 100), explosion_type='ship'))
    game._update_screen()
    assert len(game.explosions) == 1


class _FakeSound:
    """Records play/stop calls instead of touching an audio device."""

    def __init__(self):
        self.plays = 0
        self.stops = 0

    def play(self, loops=0):
        self.plays += 1

    def stop(self):
        self.stops += 1


def test_mute_key_silences_effects_and_music(game):
    _start_game(game)
    game.sounds_enabled = True
    game.shoot_sound = _FakeSound()
    game.background_music = _FakeSound()

    mute = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, unicode="m")
    game._check_keydown_events(mute)
    assert game.muted is True
    assert game.background_music.stops == 1
    game._play_sound(game.shoot_sound)
    assert game.shoot_sound.plays == 0

    game._check_keydown_events(mute)
    assert game.muted is False
    assert game.background_music.plays == 1
    game._play_sound(game.shoot_sound)
    assert game.shoot_sound.plays == 1


def test_mute_works_when_audio_is_unavailable(game):
    game.sounds_enabled = False
    game.background_music = None
    game._toggle_mute()  # must not touch the missing music object
    assert game.muted is True


def test_mute_can_be_toggled_from_the_idle_screen(game):
    press = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, unicode="m")
    game._check_keydown_events(press)
    assert game.muted is True
    game._update_screen()  # panel shows "sound (off)"


def test_unloadable_sounds_disable_audio(monkeypatch):
    monkeypatch.setattr(pygame.mixer, "Sound",
                        lambda *a, **k: (_ for _ in ()).throw(
                            pygame.error("bad file")))
    ai = AlienInvasion()
    try:
        assert ai.sounds_enabled is False
        ai._fire_bullet()  # firing must still work silently
    finally:
        pygame.quit()


def test_pause_toggle_via_keyboard(game):
    _start_game(game)
    p = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
    game._check_keydown_events(p)
    assert game.game_paused is True
    game._update_screen()  # draws the pause overlay
    game._check_keydown_events(p)
    assert game.game_paused is False
