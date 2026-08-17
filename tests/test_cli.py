"""Tests for the command-line interface and its player admin commands."""

import pygame
import pytest

import alien_invasion
from alien_invasion import AlienInvasion, main
from cli import (DEFAULT_WINDOW, apply_player_options, parse_args,
                 run_admin_commands, window_size)
from profiles import ProfileError, ProfileStore


@pytest.fixture
def store(tmp_path):
    s = ProfileStore(str(tmp_path / "profiles.json"))
    s.create("Ace")
    s.create("Bob")
    return s


# --- parsing --------------------------------------------------------------

def test_defaults_are_all_off():
    options = parse_args([])
    assert options.windowed is None
    assert options.player is None
    assert options.difficulty is None
    assert options.list_players is False
    assert options.delete_player is None


def test_windowed_without_value_uses_the_default_size():
    assert parse_args(["--windowed"]).windowed == window_size(DEFAULT_WINDOW)


@pytest.mark.parametrize("text, expected", [
    ("800x600", (800, 600)),
    (" 1920X1080 ", (1920, 1080)),
])
def test_window_size_parsing(text, expected):
    assert window_size(text) == expected


@pytest.mark.parametrize("bad", ["800", "800*600", "12x12", "axb", ""])
def test_window_size_rejects_junk(bad):
    with pytest.raises(Exception):
        window_size(bad)


@pytest.mark.parametrize("argv", [
    ["--windowed", "huge"],
    ["--difficulty", "nightmare"],
    ["--unknown-flag"],
])
def test_bad_arguments_exit_with_usage_error(argv):
    with pytest.raises(SystemExit) as exc:
        parse_args(argv)
    assert exc.value.code == 2


# --- admin commands -------------------------------------------------------

def test_list_players_prints_a_table(store, capsys):
    store.record_game(score=700, level=4)  # Bob is active
    assert run_admin_commands(parse_args(["--list-players"]), store) == 0
    out = capsys.readouterr().out
    assert "Ace" in out and "*Bob" in out
    assert "700" in out and "normal" in out


def test_list_players_with_no_players(tmp_path, capsys):
    empty = ProfileStore(str(tmp_path / "profiles.json"))
    assert run_admin_commands(parse_args(["--list-players"]), empty) == 0
    assert "No players yet." in capsys.readouterr().out


def test_delete_player_removes_and_reports(store, capsys):
    assert run_admin_commands(parse_args(["--delete-player", "Ace"]), store) == 0
    assert store.names() == ["Bob"]
    assert "Deleted Ace." in capsys.readouterr().out


def test_delete_unknown_player_is_an_error(store, capsys):
    assert run_admin_commands(parse_args(["--delete-player", "ghost"]),
                              store) == 1
    assert "error:" in capsys.readouterr().out
    assert store.names() == ["Ace", "Bob"]


def test_no_admin_command_means_play(store):
    assert run_admin_commands(parse_args([]), store) is None


# --- player/difficulty options -------------------------------------------

def test_player_option_selects_an_existing_player(store):
    apply_player_options(parse_args(["--player", "ace"]), store)
    assert store.active == "Ace"


def test_player_option_creates_a_missing_player(store):
    apply_player_options(parse_args(["--player", "Cid"]), store)
    assert store.active == "Cid"
    assert "Cid" in store.names()


def test_player_option_with_an_invalid_name_raises(store):
    with pytest.raises(ProfileError):
        apply_player_options(parse_args(["--player", "bad/name"]), store)


def test_difficulty_option_applies_to_the_chosen_player(store):
    apply_player_options(parse_args(["--player", "Ace",
                                     "--difficulty", "hard"]), store)
    assert store.stats_for("Ace")["difficulty"] == "hard"
    assert store.stats_for("Bob")["difficulty"] == "normal"


def test_no_options_leave_the_store_alone(store):
    apply_player_options(parse_args([]), store)
    assert store.active == "Bob"
    assert store.stats_for("Bob")["difficulty"] == "normal"


# --- main() ---------------------------------------------------------------

def test_main_list_players_does_not_start_the_game(capsys, monkeypatch):
    monkeypatch.setattr(alien_invasion, "AlienInvasion",
                        lambda *a, **k: pytest.fail("game should not start"))
    assert main(["--list-players"]) == 0
    assert "Player 1" in capsys.readouterr().out


def test_main_delete_player(capsys):
    ProfileStore(alien_invasion.PROFILES_FILE).create("Ace")
    assert main(["--delete-player", "Ace"]) == 0
    assert main(["--delete-player", "Ace"]) == 1  # already gone
    assert "Deleted Ace." in capsys.readouterr().out


def test_main_recreates_a_default_player_when_none_are_left(capsys):
    assert main(["--delete-player", "Player 1"]) == 0
    assert main(["--list-players"]) == 0
    assert "Player 1" in capsys.readouterr().out


def test_main_reports_an_invalid_player_name(capsys):
    assert main(["--player", "bad/name"]) == 1
    assert "error:" in capsys.readouterr().out


def test_main_starts_the_game_with_the_parsed_options(monkeypatch):
    started = {}

    class FakeGame:
        def __init__(self, options):
            started['options'] = options

        def run_game(self):
            started['ran'] = True

    monkeypatch.setattr(alien_invasion, "AlienInvasion", FakeGame)
    assert main(["--windowed", "800x600", "--player", "Cid",
                 "--difficulty", "easy"]) == 0
    assert started['ran'] is True
    assert started['options'].windowed == (800, 600)

    store = ProfileStore(alien_invasion.PROFILES_FILE)
    assert store.active == "Cid"
    assert store.difficulty == "easy"


# --- windowed mode --------------------------------------------------------

def test_windowed_option_sets_the_screen_size():
    ai = AlienInvasion(parse_args(["--windowed", "800x600"]))
    try:
        assert ai.screen.get_size() == (800, 600)
        assert (ai.settings.screen_width, ai.settings.screen_height) == (800, 600)
        ai._update_screen()  # the panel still fits and renders
    finally:
        pygame.quit()


def test_fullscreen_is_the_default(game):
    assert game.settings.screen_width == game.screen.get_rect().width
