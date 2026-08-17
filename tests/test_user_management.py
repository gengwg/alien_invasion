"""Integration tests for player management driven through the real handlers."""

import pygame
import pytest

import alien_invasion
from alien_invasion import AlienInvasion
from profiles import MAX_NAME_LENGTH, ProfileStore
from helpers import press, start_game, type_name


def _new_player(ai, name):
    """Create a player the way a user does: N, type the name, Enter."""
    press(ai, pygame.K_n)
    type_name(ai, name)
    press(ai, pygame.K_RETURN, unicode="\r")


# --- first run ------------------------------------------------------------

def test_first_run_creates_default_player(game):
    assert game.profiles.active == "Player 1"
    assert game.stats.high_score == 0


def test_first_run_migrates_legacy_high_score(isolated_data_files):
    with open(alien_invasion.HIGH_SCORE_FILE, "w") as f:
        f.write("4321")
    ai = AlienInvasion()
    try:
        assert ai.profiles.active == "Player 1"
        assert ai.stats.high_score == 4321
    finally:
        pygame.quit()


# --- creating players -----------------------------------------------------

def test_create_player_via_keyboard(game):
    _new_player(game, "Ace")
    assert game.profiles.active == "Ace"
    assert "Ace" in game.profiles.names()
    assert game.name_input is None
    assert "Ace" in game.profile_message


def test_invalid_name_keeps_prompt_open_with_message(game):
    press(game, pygame.K_n)
    type_name(game, "a/b")
    press(game, pygame.K_RETURN, unicode="\r")
    assert game.name_input == "a/b"  # still editing
    assert game.profile_message
    assert "a/b" not in game.profiles.names()


def test_duplicate_name_is_rejected(game):
    _new_player(game, "Ace")
    _new_player(game, "ace")
    assert game.profiles.names() == ["Ace", "Player 1"]
    assert "exists" in game.profile_message


def test_empty_name_is_rejected(game):
    press(game, pygame.K_n)
    press(game, pygame.K_RETURN, unicode="\r")
    assert game.name_input == ""
    assert game.profile_message


def test_name_input_is_length_capped(game):
    press(game, pygame.K_n)
    type_name(game, "a" * (MAX_NAME_LENGTH + 5))
    assert len(game.name_input) == MAX_NAME_LENGTH


def test_backspace_and_escape_during_name_entry(game):
    press(game, pygame.K_n)
    type_name(game, "Bob")
    press(game, pygame.K_BACKSPACE)
    assert game.name_input == "Bo"
    press(game, pygame.K_ESCAPE)
    assert game.name_input is None
    assert game.profile_message == ""


def test_gameplay_keys_are_text_while_naming(game):
    """'q' and 'p' must type, not quit or pause, during name entry."""
    press(game, pygame.K_n)
    type_name(game, "qp")
    assert game.name_input == "qp"
    assert game.game_paused is False


def test_profile_keys_ignored_during_play(game):
    start_game(game)
    press(game, pygame.K_n)
    assert game.name_input is None
    press(game, pygame.K_TAB)
    assert game.profiles.active == "Player 1"


# --- switching and deleting ----------------------------------------------

def test_tab_switches_player_and_high_score_display(game):
    _new_player(game, "Ace")
    game.profiles.record_game(score=800, level=4)
    game._refresh_profile_display()
    assert game.stats.high_score == 800

    press(game, pygame.K_TAB)  # -> Player 1
    assert game.profiles.active == "Player 1"
    assert game.stats.high_score == 0

    press(game, pygame.K_TAB)  # back to Ace
    assert game.profiles.active == "Ace"
    assert game.stats.high_score == 800


def test_delete_active_player_switches_to_remaining_one(game):
    _new_player(game, "Ace")
    press(game, pygame.K_DELETE)
    assert game.profiles.names() == ["Player 1"]
    assert game.profiles.active == "Player 1"
    assert "Deleted Ace" in game.profile_message


def test_cannot_start_game_without_a_player(game):
    press(game, pygame.K_DELETE)
    assert game.profiles.active is None
    start_game(game)
    assert game.stats.game_active is False
    assert "Press N" in game.profile_message
    game._update_screen()  # idle screen still renders with no players


# --- results recorded against the right player ---------------------------

def test_game_over_records_result_for_active_player(game):
    _new_player(game, "Ace")
    start_game(game)
    game.stats.score = 1200
    game.stats.level = 5
    game.stats.ships_left = 0
    game._ship_hit()

    ace = game.profiles.stats_for("Ace")
    assert ace["high_score"] == 1200
    assert ace["best_level"] == 5
    assert ace["games_played"] == 1
    assert game.profiles.stats_for("Player 1")["games_played"] == 0


def test_quitting_mid_game_records_the_result(game):
    start_game(game)
    game.stats.score = 300
    with pytest.raises(SystemExit):
        press(game, pygame.K_q)
    assert game.profiles.stats_for("Player 1")["high_score"] == 300
    assert game.profiles.stats_for("Player 1")["games_played"] == 1


def test_quitting_while_idle_records_nothing(game):
    with pytest.raises(SystemExit):
        press(game, pygame.K_q)
    assert game.profiles.stats_for("Player 1")["games_played"] == 0


def test_scores_stay_separate_across_two_games(game):
    _new_player(game, "Ace")
    start_game(game)
    game.stats.score = 900
    game.stats.ships_left = 0
    game._ship_hit()

    press(game, pygame.K_TAB)  # -> Player 1
    start_game(game)
    assert game.stats.score == 0
    assert game.stats.high_score == 0
    game.stats.score = 100
    game.stats.ships_left = 0
    game._ship_hit()

    assert game.profiles.stats_for("Ace")["high_score"] == 900
    assert game.profiles.stats_for("Player 1")["high_score"] == 100
    assert game.profiles.leaderboard() == [("Ace", 900), ("Player 1", 100)]


# --- persistence across sessions ----------------------------------------

def test_profiles_persist_to_disk_across_instances(game):
    _new_player(game, "Ace")
    start_game(game)
    game.stats.score = 500
    game.stats.ships_left = 0
    game._ship_hit()
    pygame.quit()

    reborn = AlienInvasion()
    try:
        assert reborn.profiles.active == "Ace"
        assert reborn.stats.high_score == 500
        assert reborn.profiles.names() == ["Ace", "Player 1"]
    finally:
        pygame.quit()


def test_profile_file_written_where_configured(game, isolated_data_files):
    _new_player(game, "Ace")
    path = isolated_data_files / "profiles.json"
    assert path.exists()
    assert ProfileStore(str(path)).active == "Ace"


# --- rendering ------------------------------------------------------------

def test_idle_screen_renders_panel_in_every_state(game):
    game._update_screen()  # default idle screen with leaderboard
    press(game, pygame.K_n)
    game._update_screen()  # name-entry prompt
    type_name(game, "Ace")
    press(game, pygame.K_RETURN, unicode="\r")
    game.profile_message = "some feedback"
    game._update_screen()  # message line
    start_game(game)
    game._update_screen()  # in-game scoreboard with player name
