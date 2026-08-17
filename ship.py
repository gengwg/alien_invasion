import pygame
from pygame.sprite import Sprite

from paths import resource_path

class Ship(Sprite):
    """a class to manage the ship"""

    # Class-level cache so the PNG is loaded from disk only once per
    # process, no matter how many Ship instances are created (the lives
    # HUD in the scoreboard builds several on every game/ship hit).
    _cached_image = None

    def __init__(self, ai_game):
        """initialize the ship and set its starting position"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.screen_rect = ai_game.screen.get_rect()

        # load the ship image (cached) and get its rect.
        if Ship._cached_image is None:
            Ship._cached_image = pygame.image.load(
                resource_path('images', 'spaceship.png')).convert_alpha()
        self.image = Ship._cached_image
        self.rect = self.image.get_rect()

        # start each new ship at the bottom center of the screen
        self.rect.midbottom = self.screen_rect.midbottom

        # store a decimal value for the ship's horizontal position
        self.x = float(self.rect.x)

        # movement flag
        self.moving_right = False
        self.moving_left = False

    def update(self):
        """update the ship's position based on the movement flag."""
        # update the ship's x value, not the rect.
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.x += self.settings.ship_speed
        if self.moving_left and self.rect.left > 0:
            self.x -= self.settings.ship_speed

        # update rect object from self.x
        self.rect.x = self.x

    def blitme(self):
        """draw the ship at its current location"""
        self.screen.blit(self.image, self.rect)

    def center_ship(self):
        """center the ship on the screen"""
        self.rect.midbottom = self.screen_rect.midbottom
        self.x = float(self.rect.x)
