"""Difficulty presets and their integration with player profiles."""

import pygame
import pytest

from alien_invasion import AlienInvasion
from profiles import DIFFICULTIES
from settings import DIFFICULTY_PRESETS, Settings
from helpers import press, start_game


# --- presets --------------------------------------------------------------

def test_every_difficulty_has_a_complete_preset():
    keys = {'ship_limit', 'ship_speed', 'bullet_speed', 'alien_speed',
            'autofire_cooldown', 'alien_points'}
    assert set(DIFFICULTY_PRESETS) == set(DIFFICULTIES)
    for preset in DIFFICULTY_PRESETS.values():
        assert set(preset) == keys


def test_normal_keeps_the_original_balance():
    settings = Settings()
    assert settings.difficulty == "normal"
    assert (settings.ship_limit, settings.ship_speed, settings.bullet_speed,
            settings.alien_speed, settings.alien_points) == (3, 3.5, 5.0, 2.0, 50)


def test_harder_means_faster_aliens_fewer_ships_more_points():
    easy, normal, hard = (DIFFICULTY_PRESETS[d] for d in DIFFICULTIES)
    assert easy['alien_speed'] < normal['alien_speed'] < hard['alien_speed']
    assert easy['ship_limit'] > normal['ship_limit'] > hard['ship_limit']
    assert easy['alien_points'] < normal['alien_points'] < hard['alien_points']


def test_apply_difficulty_swaps_the_preset():
    settings = Settings()
    settings.apply_difficulty("hard")
    assert settings.difficulty == "hard"
    assert settings.ship_limit == DIFFICULTY_PRESETS['hard']['ship_limit']
    assert settings.alien_speed == DIFFICULTY_PRESETS['hard']['alien_speed']


def test_apply_difficulty_ignores_unknown_names_but_still_resets():
    settings = Settings()
    settings.apply_difficulty("easy")
    settings.alien_speed = 99
    settings.apply_difficulty("nonsense")
    assert settings.difficulty == "easy"
    assert settings.alien_speed == DIFFICULTY_PRESETS['easy']['alien_speed']


def test_speedup_still_scales_from_the_preset():
    settings = Settings()
    settings.apply_difficulty("hard")
    settings.increase_speed()
    assert settings.alien_speed == pytest.approx(
        DIFFICULTY_PRESETS['hard']['alien_speed'] * settings.speedup_scale)


# --- integration with profiles -------------------------------------------

def test_d_key_cycles_difficulty_and_applies_it(game):
    assert game.settings.difficulty == "normal"
    press(game, pygame.K_d)
    assert game.profiles.difficulty == "hard"
    assert game.settings.difficulty == "hard"
    assert game.settings.ship_limit == DIFFICULTY_PRESETS['hard']['ship_limit']


def test_ship_icons_preview_the_new_difficulty_while_idle(game):
    press(game, pygame.K_d)  # -> hard
    assert game.stats.ships_left == DIFFICULTY_PRESETS['hard']['ship_limit']
    assert len(game.sb.ships) == DIFFICULTY_PRESETS['hard']['ship_limit']


def test_d_key_ignored_during_play(game):
    start_game(game)
    press(game, pygame.K_d)
    assert game.settings.difficulty == "normal"


def test_d_key_without_a_player_does_nothing(game):
    press(game, pygame.K_DELETE)  # remove the only player
    press(game, pygame.K_d)
    assert game.settings.difficulty == "normal"


def test_new_game_uses_the_players_difficulty(game):
    press(game, pygame.K_d)  # -> hard
    start_game(game)
    assert game.stats.ships_left == DIFFICULTY_PRESETS['hard']['ship_limit']
    assert game.settings.alien_points == DIFFICULTY_PRESETS['hard']['alien_points']


def test_switching_player_restores_their_difficulty(game):
    press(game, pygame.K_d)  # Player 1 -> hard
    press(game, pygame.K_n)
    for char in "Ace":
        press(game, ord(char), unicode=char)
    press(game, pygame.K_RETURN, unicode="\r")
    assert game.settings.difficulty == "normal"  # new player's default

    press(game, pygame.K_TAB)  # back to Player 1
    assert game.profiles.active == "Player 1"
    assert game.settings.difficulty == "hard"
    assert game.settings.ship_limit == DIFFICULTY_PRESETS['hard']['ship_limit']


def test_difficulty_survives_a_restart(game):
    press(game, pygame.K_d)  # -> hard
    pygame.quit()

    reborn = AlienInvasion()
    try:
        assert reborn.settings.difficulty == "hard"
        assert reborn.stats.ships_left == DIFFICULTY_PRESETS['hard']['ship_limit']
    finally:
        pygame.quit()


def test_idle_screen_shows_difficulty_hint(game):
    press(game, pygame.K_d)
    game._update_screen()  # renders the hint and stats lines without error
