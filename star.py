import pygame
from pygame.sprite import Sprite
import random

class Star(Sprite):
    """A class to represent a single star in the background."""

    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        # Create star with random size and color
        self.size = random.choice([1, 1, 1, 2])  # Mostly small stars
        self.color = (
            random.randint(200, 255),  # R
            random.randint(200, 255),  # G
            random.randint(200, 255)   # B
        )

        # Create star surface
        self.image = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color,
                         (self.size, self.size), self.size)
        self.rect = self.image.get_rect()

        # Random starting position
        self.rect.x = random.randint(0, self.settings.screen_width)
        self.rect.y = random.randint(-self.settings.screen_height, 0)

        # Vertical speed based on size
        self.speed = random.uniform(0.3, 0.8) * (1/self.size)

        # Brightness effect
        self.brightness = random.uniform(0.5, 1.5) * (1/self.size)
        self.image.set_alpha(int(255 * self.brightness))

    def update(self):
        """Move the star downward."""
        self.rect.y += self.speed

        # Reset star position if it goes off screen
        if self.rect.top > self.settings.screen_height:
            self.rect.y = random.randint(-50, 0)
            self.rect.x = random.randint(0, self.settings.screen_width)