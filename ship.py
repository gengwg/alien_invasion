import pygame

class Ship:
    """a class to manage the ship"""

    def __init__(self, ai_game):
        """initialize the ship and set its starting position"""
        self.screen = ai_game.screen
        self.screen_rect = ai_game.screen.get_rect()

        # load the ship image and get its rect.
        self.image = pygame.image.load('images/ship.bmp')
        self.rect = self.image.get_rect()

        # start each new ship at the bottom center of the screen
        self.rect.midbottom = self.screen_rect.midbottom

        # movement flag
        self.moving_right = False

    def update(self):
        """update the ship's position based on the movement flag."""
        if self.moving_right:
            self.rect.x += 1

    def blitme(self):
        """draw the ship at its current location"""

        self.screen.blit(self.image, self.rect)
