from profiles import DEFAULT_DIFFICULTY

# Per-difficulty starting values. "normal" is the game's original balance;
# easy gives more lives and slower aliens, hard the reverse and more points.
DIFFICULTY_PRESETS = {
    'easy': {
        'ship_limit': 5,
        'ship_speed': 4.0,
        'bullet_speed': 6.0,
        'alien_speed': 1.5,
        'autofire_cooldown': 400,
        'alien_points': 30,
    },
    'normal': {
        'ship_limit': 3,
        'ship_speed': 3.5,
        'bullet_speed': 5.0,
        'alien_speed': 2.0,
        'autofire_cooldown': 500,
        'alien_points': 50,
    },
    'hard': {
        'ship_limit': 2,
        'ship_speed': 3.0,
        'bullet_speed': 4.5,
        'alien_speed': 3.0,
        'autofire_cooldown': 650,
        'alien_points': 100,
    },
}


class Settings:
    """a class to store all settings for Alien Invasion"""

    def __init__(self):
        """initialize the game's static settings"""
        self.difficulty = DEFAULT_DIFFICULTY
        # screen settings
        self.screen_width = 1200
        self.screen_height = 800
        # self.bg_color = (230, 230, 230)   # light gray
        self.bg_color = (10, 10, 30)     # dark space blue

        # bullet settings
        self.bullet_width = 5    # narrow core
        self.bullet_height = 20  # short beam
        self.bullet_glow_width = 15  # glow effect
        self.bullet_core_color = (255, 50, 50)    # bright red
        self.bullet_glow_color = (255, 100, 100, 30)  # translucent glow
        self.bullet_trail_color = (255, 50, 50)
        self.bullets_allowed = 30    # numbers of bullets allowed on screen

        # star background settings
        self.star_count = 100

        # alien settings
        self.fleet_drop_speed = 10

        # how quickly the game speeds up
        self.speedup_scale = 1.1

        # how quickly the alien point values increase
        self.score_scale = 1.5

        self.initialize_dynamic_settings()

    def apply_difficulty(self, difficulty):
        """switch to a difficulty preset and reset the dynamic settings."""
        if difficulty in DIFFICULTY_PRESETS:
            self.difficulty = difficulty
        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """initialize settings that change throughout the game"""
        preset = DIFFICULTY_PRESETS[self.difficulty]
        self.ship_limit = preset['ship_limit']
        self.ship_speed = preset['ship_speed']
        self.bullet_speed = preset['bullet_speed']
        self.alien_speed = preset['alien_speed']
        self.autofire_cooldown = preset['autofire_cooldown']

        # fleet direction of 1 represents right; -1 represents left.
        self.fleet_direction = 1

        # scoring
        self.alien_points = preset['alien_points']

    def increase_speed(self):
        """increase speed settings and alien point values"""
        self.ship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale
        self.autofire_cooldown /= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
