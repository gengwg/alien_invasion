class Settings:
    """a class to store all settings for Alien Invasion"""

    def __init__(self):
        """initialize the game's settings"""
        # screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (230, 230, 230)

        # ship settings
        self.ship_speed = 1.5
        self.ship_limit = 3

        # bullet settings
        self.bullet_speed = 1.5 # bullets travel slower than ship
        self.bullet_width = 3   # width 3 pixels
        self.bullet_height = 15 # height 15 pixels
        self.bullet_color = (60, 60, 60)    # dark gray
        self.bullets_allowed = 300    # numbers of bullets allowed on screen

        # alien settings
        self.alien_speed = 1.0
        self.fleet_drop_speed = 50
        # fleet direction of 1 represents right; -1 represents left.
        self.fleet_direction = 1
