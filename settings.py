class Settings:
    """a class to store all settings for Alien Invasion"""

    def __init__(self):
        """initialize the game's static settings"""
        # screen settings
        self.screen_width = 1200
        self.screen_height = 800
        # self.bg_color = (230, 230, 230)   # light gray
        self.bg_color = (10, 10, 30)     # dark space bulue

        # ship settings
        self.ship_limit = 3

        # bullet settings
        self.bullet_width = 5   # width 3 pixels
        self.bullet_height = 20 # height 15 pixels
        self.bullet_color = (100, 255, 255)
        self.bullets_allowed = 30    # numbers of bullets allowed on screen

        # alien settings
        self.fleet_drop_speed = 10

        # how quickly the game speeds up
        self.speedup_scale = 1.2

        # how quickly the alien point values increase
        self.score_scale = 1.5

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """initialize settings that change throughout the game"""
        self.ship_speed = 3.5
        self.bullet_speed = 4.0
        self.alien_speed = 2.0

        # fleet direction of 1 represents right; -1 represents left.
        self.fleet_direction = 1

        # scoring
        self.alien_points = 50


    def increase_speed(self):
        """increase speed settings and alien point values"""
        self.ship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
