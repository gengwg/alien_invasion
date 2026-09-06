# Alien Invasion Game

A classic space shooter game built with Pygame. Defend Earth from alien fleets and achieve the highest score!

![screenshot](images/screenshot.png)

## Installation

### Prerequisites

- Python 3.8+
- Either [uv](https://docs.astral.sh/uv/) **or** plain `python3 -m venv` + `pip`

### Option A — uv (recommended)

`uv` manages the virtual environment and installs `pygame-ce` for you, so it
works on Linux distros that block system-wide `pip` (PEP 668 /
"externally-managed-environment") and on Windows and macOS:

```bash
uv run alien_invasion.py --list-players   # first run resolves+installs deps
uv run alien_invasion.py                  # play the game
```

All other flags work too, e.g. `uv run alien_invasion.py --windowed`.

### Option B — venv + pip

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python alien_invasion.py
```

> `requirements.txt` pins `pygame-ce`, a drop-in `pygame` replacement with
> prebuilt wheels for modern Python on Linux, Windows and macOS.

## How to Play

### Running the Game

```bash
python alien_invasion.py                      # fullscreen
python alien_invasion.py --windowed           # 1200x800 window
python alien_invasion.py --windowed 800x600   # custom window size
python alien_invasion.py --player Ace --difficulty hard
python alien_invasion.py --list-players       # show saved players, then exit
python alien_invasion.py --delete-player Ace  # remove a player, then exit
```

If you installed with **uv**, replace `python` with `uv run` in the commands
above, e.g. `uv run alien_invasion.py --windowed 800x600`.

`--player` creates the player if they don't exist yet.

### Controls

| Key       | Action                           |
| --------- | -------------------------------- |
| **← →**   | Move spaceship left/right        |
| **SPACE** | Toggle auto-fire on/off           |
| **P**     | Pause/Unpause game               |
| **M**     | Mute/Unmute sound                |
| **ENTER** | Start new game                   |
| **Q**     | Quit game (saves your progress)  |

On the start screen you also manage players:

| Key       | Action                                              |
| --------- | --------------------------------------------------- |
| **N**     | New player (type a name, ENTER to confirm, ESC cancels) |
| **TAB**   | Switch to the next player                           |
| **D**     | Cycle difficulty: normal → hard → easy              |
| **DEL**   | Delete the current player                           |

## Game Features

- 🚀 Progressive difficulty: Speed increases with each level, at a steady 60 FPS
- 🖥️ Fullscreen or windowed (`--windowed`)
- 💥 Explosion effects for alien/ship destruction
- 🔊 Sound effects and background music
- 🌟 Starry animated background
- 👥 Player profiles: each player keeps their own high score, best level, games played and difficulty
- 🎚️ Three difficulties: easy, normal (the original balance) and hard
- 🏆 Top-pilots leaderboard on the start screen
- ⏸️ Pause functionality and a mute toggle

Profiles live in `profiles.json` next to the game. An older `high_score.txt`
is imported once into the first profile.

## Tests

```bash
python -m pytest tests/ -v          # headless, no display or audio needed
python tests/coverage_report.py     # line coverage per module (stdlib only)
```

With `uv`: `uv run --with pytest python -m pytest tests/ -v`.

## Platform notes

- **Windows:** the game runs unchanged. Use `pygame-ce` from `requirements.txt`
  (it ships Windows wheels), and note that double-clicking runs fullscreen — add
  `--windowed` (or a shortcut that passes it) if you prefer a window.
- **Linux (Wayland):** the game prefers SDL's native Wayland backend to avoid a
  hard crash in the X11/GLX path on some NVIDIA setups.

## Troubleshooting

1. **`X Error ... BadValue ... GLX` / black window on Linux:** force a video
   backend with the `SDL_VIDEODRIVER` variable, e.g.
   `SDL_VIDEODRIVER=wayland uv run alien_invasion.py --windowed` or
   `SDL_VIDEODRIVER=x11 ...`. The game already picks Wayland automatically when
   it detects a Wayland session.
2. **Fullscreen fails to open:** run with `--windowed` (it also falls back to a
   scaled window automatically when a requested mode is unavailable).
3. **`error: externally-managed-environment` (pip):** use **uv** (Option A) or a
   `venv` (Option B) above instead of system `pip`.
4. **If sounds don't play:**
   - Ensure `.wav/.ogg` files exist in `sounds/`
   - Check system volume/mute status
5. **If missing images:**
   - Verify ship and alien images exist in `images/`
6. **On Linux, install SDL dependencies (only if your `pygame-ce` build needs
   them):**

```bash
sudo apt-get install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

Destroy alien waves, survive as long as possible, and top the leaderboard! 👾🛸