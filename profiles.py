"""Player profiles: per-player high scores and stats, stored as JSON.

Profiles are keyed by lower-cased name so "Ace" and "ACE" are the same
player, while the display spelling the player typed is preserved.
"""

import json
import os
import re

MAX_NAME_LENGTH = 12
DEFAULT_PLAYER_NAME = "Player 1"

_NAME_RE = re.compile(r"^[A-Za-z0-9 _-]+$")

_EMPTY_STATS = {
    "high_score": 0,
    "best_level": 0,
    "games_played": 0,
    "total_score": 0,
}


class ProfileError(ValueError):
    """A player name is invalid, unknown, or already taken."""


def normalize_name(name):
    """Return a cleaned-up player name, or raise ProfileError."""
    cleaned = " ".join(str(name).split())
    if not cleaned:
        raise ProfileError("Name cannot be empty.")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ProfileError(f"Name cannot exceed {MAX_NAME_LENGTH} characters.")
    if not _NAME_RE.match(cleaned):
        raise ProfileError("Use letters, digits, spaces, '_' or '-' only.")
    return cleaned


def _clean_record(name, raw):
    """Build a valid record from possibly-corrupt stored data."""
    record = dict(_EMPTY_STATS, name=name)
    if isinstance(raw, dict):
        for key in _EMPTY_STATS:
            value = raw.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                record[key] = value
    return record


class ProfileStore:
    """Load, mutate, and persist the set of player profiles."""

    def __init__(self, path):
        self.path = path
        self._players = {}
        self._active_key = None
        self._load()

    # --- persistence -----------------------------------------------------

    def _load(self):
        try:
            with open(self.path, 'r') as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return

        players = data.get("players")
        if isinstance(players, dict):
            for key, raw in players.items():
                if not isinstance(raw, dict):
                    continue
                name = raw.get("name")
                try:
                    name = normalize_name(name if name else key)
                except ProfileError:
                    continue
                self._players[name.lower()] = _clean_record(name, raw)

        active = data.get("active")
        if isinstance(active, str) and active.lower() in self._players:
            self._active_key = active.lower()

    def save(self):
        """Write profiles to disk atomically; never raise on I/O failure."""
        data = {
            "active": self.active,
            "players": self._players,
        }
        tmp_path = self.path + '.tmp'
        try:
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)
        except OSError as e:
            print(f"Warning: could not save profiles ({e}).")
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    def ensure_default(self, legacy_high_score_file=None):
        """Create a starter profile on first run, importing any old score."""
        if self._players:
            return
        self.create(DEFAULT_PLAYER_NAME)
        if legacy_high_score_file:
            try:
                with open(legacy_high_score_file, 'r') as f:
                    self._active_record()["high_score"] = max(int(f.read()), 0)
            except (OSError, ValueError):
                pass
        self.save()

    # --- queries ---------------------------------------------------------

    @property
    def active(self):
        """Display name of the active player, or None."""
        record = self._active_record()
        return record["name"] if record else None

    @property
    def high_score(self):
        """High score of the active player (0 if there is none)."""
        record = self._active_record()
        return record["high_score"] if record else 0

    def names(self):
        """Display names of all players, sorted case-insensitively."""
        return [self._players[key]["name"] for key in sorted(self._players)]

    def stats_for(self, name):
        """Return a copy of a player's stats, or raise ProfileError."""
        return dict(self._require(name))

    def leaderboard(self, limit=5):
        """Top (name, high_score) pairs, highest first, name breaking ties."""
        ranked = sorted(self._players.values(),
                        key=lambda r: (-r["high_score"], r["name"].lower()))
        return [(r["name"], r["high_score"]) for r in ranked[:limit]]

    # --- mutations -------------------------------------------------------

    def create(self, name):
        """Create a player, make them active, and return the stored name."""
        name = normalize_name(name)
        if name.lower() in self._players:
            raise ProfileError(f"'{name}' already exists.")
        self._players[name.lower()] = _clean_record(name, None)
        self._active_key = name.lower()
        self.save()
        return name

    def select(self, name):
        """Make an existing player active and return their name."""
        record = self._require(name)
        self._active_key = record["name"].lower()
        self.save()
        return record["name"]

    def select_next(self):
        """Activate the next player in name order; return them, or None."""
        keys = sorted(self._players)
        if not keys:
            return None
        try:
            index = keys.index(self._active_key)
        except ValueError:
            index = -1
        self._active_key = keys[(index + 1) % len(keys)]
        self.save()
        return self.active

    def delete(self, name):
        """Delete a player, activating another one if the active one went."""
        record = self._require(name)
        key = record["name"].lower()
        del self._players[key]
        if self._active_key == key:
            remaining = sorted(self._players)
            self._active_key = remaining[0] if remaining else None
        self.save()

    def record_game(self, score, level):
        """Fold a finished game's result into the active player's stats."""
        record = self._active_record()
        if not record:
            return
        record["high_score"] = max(record["high_score"], int(score))
        record["best_level"] = max(record["best_level"], int(level))
        record["games_played"] += 1
        record["total_score"] += max(int(score), 0)
        self.save()

    # --- helpers ---------------------------------------------------------

    def _active_record(self):
        return self._players.get(self._active_key) if self._active_key else None

    def _require(self, name):
        try:
            key = normalize_name(name).lower()
        except ProfileError:
            key = None
        if key not in self._players:
            raise ProfileError(f"No such player: {name}")
        return self._players[key]
