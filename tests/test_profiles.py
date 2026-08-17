"""Unit tests for the player profile store (no pygame needed)."""

import json

import pytest

from profiles import ProfileError, ProfileStore, normalize_name


@pytest.fixture
def store(tmp_path):
    return ProfileStore(str(tmp_path / "profiles.json"))


# --- name validation -----------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("gengwg", "gengwg"),
    ("  Ace  ", "Ace"),
    ("Red   Baron", "Red Baron"),
    ("p1_2-3", "p1_2-3"),
])
def test_normalize_name_accepts_valid(raw, expected):
    assert normalize_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "a" * 13, "bad/name", "nope!", "\n"])
def test_normalize_name_rejects_invalid(raw):
    with pytest.raises(ProfileError):
        normalize_name(raw)


# --- create / select / delete -------------------------------------------

def test_create_selects_new_player(store):
    store.create("Ace")
    assert store.active == "Ace"
    assert store.names() == ["Ace"]
    assert store.high_score == 0


def test_create_rejects_duplicate_ignoring_case(store):
    store.create("Ace")
    with pytest.raises(ProfileError):
        store.create("ACE")
    assert store.names() == ["Ace"]


def test_names_sorted_case_insensitively(store):
    for name in ("zoe", "Ace", "bob"):
        store.create(name)
    assert store.names() == ["Ace", "bob", "zoe"]


def test_select_switches_active_player(store):
    store.create("Ace")
    store.create("Bob")
    store.select("ace")
    assert store.active == "Ace"


def test_select_unknown_player_raises(store):
    with pytest.raises(ProfileError):
        store.select("nobody")


def test_select_next_cycles_through_players(store):
    for name in ("Ace", "Bob", "Cid"):
        store.create(name)
    store.select("Ace")
    assert store.select_next() == "Bob"
    assert store.select_next() == "Cid"
    assert store.select_next() == "Ace"


def test_select_next_with_no_players_returns_none(store):
    assert store.select_next() is None


def test_delete_active_falls_back_to_another_player(store):
    store.create("Ace")
    store.create("Bob")  # active
    store.delete("Bob")
    assert store.active == "Ace"
    assert store.names() == ["Ace"]


def test_delete_last_player_clears_active(store):
    store.create("Ace")
    store.delete("Ace")
    assert store.active is None
    assert store.names() == []
    assert store.high_score == 0


def test_delete_unknown_player_raises(store):
    with pytest.raises(ProfileError):
        store.delete("ghost")


# --- recording results ---------------------------------------------------

def test_record_game_updates_stats(store):
    store.create("Ace")
    store.record_game(score=500, level=3)
    store.record_game(score=200, level=5)
    stats = store.stats_for("Ace")
    assert stats["high_score"] == 500
    assert stats["best_level"] == 5
    assert stats["games_played"] == 2
    assert stats["total_score"] == 700
    assert store.high_score == 500


def test_record_game_without_active_player_is_noop(store):
    store.record_game(score=100, level=2)
    assert store.names() == []


def test_record_game_isolates_players(store):
    store.create("Ace")
    store.record_game(score=900, level=4)
    store.create("Bob")
    assert store.high_score == 0
    store.record_game(score=100, level=1)
    assert store.stats_for("Ace")["high_score"] == 900
    assert store.stats_for("Bob")["high_score"] == 100


def test_leaderboard_orders_by_high_score(store):
    for name, score in (("Ace", 300), ("Bob", 900), ("Cid", 600)):
        store.create(name)
        store.record_game(score=score, level=1)
    assert store.leaderboard() == [("Bob", 900), ("Cid", 600), ("Ace", 300)]
    assert store.leaderboard(limit=2) == [("Bob", 900), ("Cid", 600)]


# --- persistence ---------------------------------------------------------

def test_save_and_reload_round_trip(tmp_path):
    path = str(tmp_path / "profiles.json")
    store = ProfileStore(path)
    store.create("Ace")
    store.record_game(score=450, level=2)
    store.create("Bob")
    store.save()

    reloaded = ProfileStore(path)
    assert reloaded.names() == ["Ace", "Bob"]
    assert reloaded.active == "Bob"
    assert reloaded.stats_for("Ace")["high_score"] == 450


def test_save_leaves_no_temp_file(tmp_path):
    path = str(tmp_path / "profiles.json")
    store = ProfileStore(path)
    store.create("Ace")
    store.save()
    assert [p.name for p in tmp_path.iterdir()] == ["profiles.json"]


def test_corrupt_file_falls_back_to_empty_store(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text("{not json")
    store = ProfileStore(str(path))
    assert store.names() == []
    assert store.active is None


def test_partially_bad_records_are_repaired(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({
        "active": "Ace",
        "players": {
            "ace": {"name": "Ace", "high_score": "oops"},
            "bob": "not a dict",
        },
    }))
    store = ProfileStore(str(path))
    assert store.names() == ["Ace"]
    assert store.stats_for("Ace")["high_score"] == 0
    assert store.stats_for("Ace")["games_played"] == 0


def test_non_dict_file_contents_ignored(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text("[1, 2, 3]")
    assert ProfileStore(str(path)).names() == []


def test_stored_record_with_invalid_name_is_skipped(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({
        "players": {"bad": {"name": "bad/name"}, "ace": {"name": "Ace"}},
    }))
    assert ProfileStore(str(path)).names() == ["Ace"]


def test_select_next_from_no_active_player_picks_first(tmp_path):
    path = str(tmp_path / "profiles.json")
    store = ProfileStore(path)
    store.create("Bob")
    store.create("Ace")
    store.delete("Ace")
    store.delete("Bob")  # active is now None
    store.create("Zoe")
    store._active_key = None
    assert store.select_next() == "Zoe"


def test_lookup_with_invalid_name_raises(store):
    store.create("Ace")
    for bad in ("bad/name", ""):
        with pytest.raises(ProfileError):
            store.select(bad)
        with pytest.raises(ProfileError):
            store.stats_for(bad)
        with pytest.raises(ProfileError):
            store.delete(bad)


def test_active_pointing_at_missing_player_is_dropped(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({"active": "ghost", "players": {}}))
    assert ProfileStore(str(path)).active is None


def test_unwritable_path_does_not_raise(tmp_path):
    store = ProfileStore(str(tmp_path / "missing_dir" / "profiles.json"))
    store.create("Ace")
    store.save()  # must not raise


# --- first-run setup / legacy migration ---------------------------------

def test_ensure_default_creates_player_and_imports_legacy_score(tmp_path):
    legacy = tmp_path / "high_score.txt"
    legacy.write_text("1234")
    store = ProfileStore(str(tmp_path / "profiles.json"))
    store.ensure_default(str(legacy))
    assert store.active == "Player 1"
    assert store.high_score == 1234


def test_ensure_default_tolerates_missing_or_corrupt_legacy_file(tmp_path):
    legacy = tmp_path / "high_score.txt"
    legacy.write_text("garbage")
    store = ProfileStore(str(tmp_path / "profiles.json"))
    store.ensure_default(str(legacy))
    assert store.high_score == 0

    store2 = ProfileStore(str(tmp_path / "other.json"))
    store2.ensure_default(str(tmp_path / "nope.txt"))
    assert store2.active == "Player 1"
    assert store2.high_score == 0


def test_ensure_default_keeps_existing_players(tmp_path):
    path = str(tmp_path / "profiles.json")
    store = ProfileStore(path)
    store.create("Ace")
    store.save()

    reloaded = ProfileStore(path)
    reloaded.ensure_default(None)
    assert reloaded.names() == ["Ace"]
    assert reloaded.active == "Ace"
