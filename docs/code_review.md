# Code Review — Alien Invasion

**Date:** 2025-08-17
**Scope:** Full repository review (all 10 Python modules, README, assets, project layout)
**Reviewer:** Automated code review (dsh agent)

---

## 1. Project Summary

A single-player space shooter built with Pygame, based on the *Python Crash Course* "Alien Invasion"
project and extended with extra features: fullscreen mode, auto-fire, pause, particle explosions,
a scrolling starfield, sound effects, background music, and persistent high-score storage.

| File | Role |
| ---- | ---- |
| `alien_invasion.py` | Main game class, event loop, collisions, fleet management |
| `settings.py` | Static + dynamic (per-level) configuration |
| `ship.py` | Player ship sprite and movement |
| `alien.py` | Alien sprite and fleet movement |
| `bullet.py` | Laser projectile with glow/trail rendering |
| `explosion.py` | Particle-based explosion effect (alien & ship variants) |
| `star.py` | Background starfield sprites |
| `scoreboard.py` | Score / high score / level / remaining-ships HUD |
| `button.py` | "Play" button |
| `game_stats.py` | Game state statistics and high-score loading |

**Positives up front:**

- Clean module separation; each sprite class is small and focused.
- Consistent use of `pygame.sprite.Group` for bullets, aliens, stars, explosions.
- Good feature set for a learning project: difficulty scaling, pause, persistent high score.
- All 10 modules pass `py_compile` (Python 3.14).
- `.gitignore` properly excludes `high_score.txt` and Python build artifacts.

---

## 2. Critical Bugs

These will cause a crash or visibly wrong behavior and should be fixed first.

### 2.1 Starting level is 10, not 1 — `game_stats.py:23`

```python
def reset_stats(self):
    self.ships_left = self.settings.ship_limit
    self.score = 0
    self.level = 10   # <-- almost certainly leftover debug code
```

Every new game begins at **Level 10**. Combined with the next bug, this is even worse.

### 2.2 Speeds are compounded 10× on every new game — `alien_invasion.py:229-231`

```python
# apply speed increases for previous levels
for _ in range(self.stats.level):
    self.settings.increase_speed()
```

Because `reset_stats()` sets `level = 10`, clicking Play calls `increase_speed()` **ten times**
(`1.1^10 ≈ 2.6×` on all speeds and `50 × 1.5^10 ≈ 2883` points per alien) before the first
alien appears. This looks like a workaround someone added to "honor" the hard-coded level 10 —
both should be removed: start at `level = 1` and delete this loop (difficulty should scale
when a fleet is cleared, which `_check_bullet_alien_collisions` already does).

### 2.3 High score is lost when the game ends normally — `alien_invasion.py:189-192`

`_save_high_score()` is only called from the QUIT handler and the `q` key. When the player
loses their last ship (`self.stats.game_active = False`), the game returns to the Play
screen without saving. Closing the window from that screen does trigger the QUIT handler,
but any crash, kill, or `sys.exit()` path that bypasses `_check_events` loses the score.
Save the high score in `_ship_hit()`'s `else` branch (game over) as well.

### 2.4 No error handling around resource loading

All of these crash with a raw traceback if the file is missing or the CWD is wrong:

- `pygame.mixer.Sound(...)` × 4 — `alien_invasion.py:83-86`
- `pygame.image.load(...)` — `ship.py:15`, `alien.py:15`
- `open('high_score.txt', 'w')` — `alien_invasion.py:274` (unhandled `OSError`; also the
  read path in `game_stats.py:15` crashes on a *corrupt* file — `int(f.read())` raises
  `ValueError`, which is not caught; only `FileNotFoundError` is).

Additionally, all paths are **relative to the current working directory**, so the game only
works when launched from the repo root. Use paths anchored to the script location, e.g.
`os.path.join(os.path.dirname(__file__), 'images', 'spaceship.png')` or `pathlib`.

### 2.5 `pygame.mixer.init()` can fail on machines without audio — `alien_invasion.py:48`

`pygame.mixer.init()` raises `pygame.error` when no audio device exists (common on headless
Linux/CI). Wrap it and skip sound loading gracefully.

---

## 3. Functional / Logic Issues

### 3.1 Explosions freeze while paused or on the title screen

`_update_explosions()` is only called inside `if self.stats.game_active and not
self.game_paused` (`alien_invasion.py:103-108`). When the ship is destroyed and the game
ends, the ship explosion stops animating mid-flight — particles hang frozen on the title
screen. Explosion updates should run unconditionally (they are purely visual).

### 3.2 Stars keep scrolling while paused

`_update_stars()` runs before the pause check, so the background keeps moving during pause.
Minor, but inconsistent with "Game Paused" semantics.

### 3.3 `sleep(1.0)` blocks the whole loop — `alien_invasion.py:188`

After a ship hit, `time.sleep(1.0)` freezes the entire process: no events are pumped, so the
window is unresponsive (and on some platforms marked "not responding") for a second. Use a
pygame timer/state flag instead.

### 3.4 Pause and auto-fire state leak across games

- `game_paused` is not reset in `_check_play_button`; starting a new game while paused leaves
  the new game paused.
- `autofire_active` also survives game over / restart.

### 3.5 `check_edges()` implicitly returns `None` — `alien.py:30-34`

Works because `None` is falsy, but the method should explicitly `return False`.

### 3.6 Bullet settings are dead code — `settings.py:16-18` vs `bullet.py:19-21`

`Settings` defines `bullet_width`, `bullet_height`, `bullet_color`, but `Bullet` hard-codes
its own `width = 5`, `height = 20`, and colors. Either wire the settings through or delete
them from `Settings` to avoid a false sense of configurability.

### 3.7 Star count is a magic number in two places

`100` appears in both `_create_star_background` and `_update_stars`
(`alien_invasion.py:63, 77`). Move it to `Settings` (e.g. `star_count`). Note also that
`Star.update()` already recycles off-screen stars to the top, so the remove-and-refill logic
in `_update_stars` is redundant — the count never actually drops.

### 3.8 README inconsistencies

- The controls table says **SPACE** "Toggle auto-fire (hold to shoot)" — it is a toggle
  (KEYDOWN flips the flag), and KEYUP always clears it, so "hold" is wrong; describing it as
  a toggle is correct, "hold" is not.
- Line 64 has a dangling, misspelled reference-style link definition:
  `[def]: 'images/screnshot.png'` (screenshot is already embedded on line 5). Remove it.
- Missing features listed vs. implemented is fine, but there is no `requirements.txt`
  (see §5).

---

## 4. Code Quality / Maintainability

### 4.1 Dead and commented-out code

- `alien_invasion.py:24-26` — commented windowed-mode `set_mode` call.
- `alien_invasion.py:121` — commented `print(len(self.bullets))`.
- `alien_invasion.py:131` — commented-out alternate `groupcollide` arguments.
- `alien_invasion.py:161` — commented `print("Ship hit!!!")`.
- `alien_invasion.py:276` — commented `print("High score saved.")`.
- `alien_invasion.py:369-370` — commented-out explosion update/draw.
- `alien.py:14` — commented-out old BMP load.
- `bullet.py:16` — `self.trail_color` includes an alpha value but is used with
  `pygame.draw.circle` directly on the display surface (24-bit), so the alpha is ignored;
  either draw on a SRCALPHA surface or drop the 4th component.
- Unused assets in the repo: `images/alien.bmp`, `images/ship.bmp`,
  `images/Spaceship_tut.png`, `images/playerShip2_red.png`, `sounds/DeathFlash.flac`
  (referenced nowhere). Either use them or remove them (~150 KB of dead weight).

### 4.2 Typos in comments / docstrings

- `alien_invasion.py:117` — "reahc" → reach
- `alien_invasion.py:338` — "entiere" → entire
- `alien_invasion.py:349` — "passs" → pass
- `settings.py:10` — "bulue" → blue
- `bullet.py:1` — leftover template header `# [file name]: bullet.py`

### 4.3 Style consistency

- Mixed docstring conventions: some classes/methods use `"""..."""`, several methods in
  `alien_invasion.py` (`_create_alien`, `update` in `Explosion`/`Star` are fine) lack
  docstrings or have inconsistent capitalization ("overall class to manage...", "a class
  to store...").
- No module-level docstrings anywhere.
- No `if __name__ == "__main__"` guard issues — the main guard is present and correct.
- `button.py` imports `pygame.font` only; fine, but `pygame.font.SysFont(None, 36, bold=True)`
  silently falls back to a default font on all platforms — acceptable, but font creation on
  every pause frame in `_update_screen` (line 374) is wasteful; create the font once.

### 4.4 Performance notes (minor for this scale)

- `prep_ships()` instantiates full `Ship` objects (loading the PNG from disk each time) just
  to show life icons — `Ship.__init__` calls `pygame.image.load` every time. Cache the image
  at class level or load once in `Scoreboard` and blit it directly.
- Pause text font is re-created every frame while paused (§4.3).
- Star surfaces are tiny and created once — fine.

### 4.5 Structure suggestions

- `alien_invasion.py` is doing a lot (event handling, collisions, fleet creation, sound,
  rendering). Consider extracting sound loading into a small `audio.py` helper with
  graceful-degradation, and high-score load/save into `game_stats.py` (load already lives
  there; save lives in the main class — inconsistent).
- `Explosion` defines `self.image`/`self.rect` as required Sprite attributes but then draws
  particles manually via `draw(screen)` rather than through the group's `draw()` — the
  `image` is never updated. Harmless, but either use the sprite protocol fully or don't
  inherit from `Sprite` for the image parts.

---

## 5. Testing, Packaging, Repo Hygiene

- **No tests at all.** Even for a game, the pure-logic pieces are testable:
  `Settings.increase_speed`, `GameStats.reset_stats`, score rounding in `Scoreboard`
  (with a stubbed font), fleet sizing math in `_create_fleet`. Consider adding `pytest`
  with a dummy video driver (`SDL_VIDEODRIVER=dummy`) for CI.
- **No `requirements.txt` / `pyproject.toml`.** The README pins "Pygame 2.1.2+" in prose
  only. Add `requirements.txt` with `pygame>=2.1.2`.
- **No license header issue:** `LICENSE` (Apache-2.0) is present — good.
- README screenshot (`images/screenshot.png`) exists and is referenced correctly — good.
- Git history is clean and incremental; commit messages are descriptive — good.

---

## 6. Security / Robustness

- `int(f.read())` on `high_score.txt` (game_stats.py:15): a hand-edited or corrupted file
  crashes the game. Catch `(FileNotFoundError, ValueError)`.
- `_save_high_score` writes directly to `high_score.txt`; a crash mid-write truncates it.
  Write to a temp file and rename for atomicity (low priority for a game, but trivial).
- No network or input-parsing attack surface otherwise — fine for a local game.

---

## 7. Prioritized Recommendations

| # | Severity | Action |
| - | -------- | ------ |
| 1 | **High** | Set `self.level = 1` in `reset_stats` and delete the speed-compounding loop in `_check_play_button` (§2.1, §2.2) |
| 2 | **High** | Save the high score at game over, not only on quit (§2.3) |
| 3 | **High** | Anchor all asset paths to the script directory; add try/except around image/sound/high-score I/O (§2.4, §6) |
| 4 | **High** | Guard `pygame.mixer.init()` for audio-less environments (§2.5) |
| 5 | Medium | Update explosions regardless of pause/game-active state (§3.1); decide whether stars should pause too (§3.2) |
| 6 | Medium | Replace blocking `sleep(1.0)` with a timed state (§3.3) |
| 7 | Medium | Reset `game_paused` and `autofire_active` when starting a new game (§3.4) |
| 8 | Medium | Reconcile bullet settings vs hard-coded values; move star count into Settings; remove redundant star refill (§3.6, §3.7) |
| 9 | Low | Remove dead/commented code, unused assets, fix comment typos, fix README (§4.1, §4.2, §3.8) |
| 10 | Low | Add `requirements.txt`, minimal pytest coverage, cache the ship image for the lives HUD, cache the pause font (§5, §4.4) |
| 11 | Low | Add explicit `return False` in `Alien.check_edges` (§3.5); make high-score write atomic (§6) |

---

## 8. Overall Conclusion

This is a well-organized learning project that goes meaningfully beyond its tutorial origin —
the starfield, particle explosions, auto-fire, pause, and sound design show real initiative.
The architecture (one class per sprite type, a central game class, settings/stats split) is
sound and easy to extend.

The most damaging problems are **two interacting bugs that corrupt game balance**
(starting level 10 + tenfold speed compounding) and **fragile resource handling**
(relative paths, no I/O error handling, unguarded mixer init), all of which are small,
low-risk fixes. After that, the codebase would benefit most from deleting dead code,
reconciling duplicated configuration, and adding a minimal test/packaging baseline.

**Verdict:** solid foundation; fix items 1–4 before shipping or sharing, items 5–8 for
polish, and the rest as housekeeping.
