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

        # bullet settings
        self.bullet_speed = 1.0 # bullets travel slower than ship
        self.bullet_width = 3   # width 3 pixels
        self.bullet_height = 15 # height 15 pixels
        self.bullet_color = (60, 60, 60)    # dark gray
        self.bullets_allowed = 300    # numbers of bullets allowed on screen

        # alien settings
        self.alien_speed = 1.0
