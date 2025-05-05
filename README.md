# Alien Invasion Game

A classic space shooter game built with Pygame. Defend Earth from alien fleets and achieve the highest score!

## Installation

### Prerequisites
- Python 3.7+
- Pygame 2.1.2+

1. Clone/download the repository
2. Install dependencies:

```bash
pip install pygame
```

## How to Play

### Running the Game
```bash
python alien_invasion.py
```

### Controls
| Key       | Action                           |
| --------- | -------------------------------- |
| **← →**   | Move spaceship left/right        |
| **SPACE** | Toggle auto-fire (hold to shoot) |
| **P**     | Pause/Unpause game               |
| **ENTER** | Start new game                   |
| **Q**     | Quit game (saves high score)     |

## Game Features
- 🚀 Progressive difficulty: Speed increases with each level
- 💥 Explosion effects for alien/ship destruction
- 🔊 Sound effects and background music
- 🌟 Starry animated background
- 🏆 Persistent high score tracking
- ⏸️ Pause functionality

## Troubleshooting
1. If sounds don't play:
   - Ensure `.wav/.ogg` files exist in `sounds/`
   - Check system volume/mute status
2. If missing images:
   - Verify ship and alien images exist in `images/`
3. On Linux systems, install SDL dependencies:
```bash
sudo apt-get install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

Destroy alien waves, survive as long as possible, and top the leaderboard! 👾🛸
