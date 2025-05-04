# [file name]: bullet.py
import pygame
from pygame.sprite import Sprite

class Bullet(Sprite):
    """A class to manage laser beams fired from the ship."""

    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        # Laser colors
        self.core_color = (255, 50, 50)    # Bright red
        self.glow_color = (255, 150, 150)  # Light red
        self.trail_color = (255, 50, 50, 50)  # Transparent trail

        # Create laser dimensions
        self.width = 5   # Narrow core
        self.height = 20  # Short beam
        self.glow_width = 15  # Glow effect

        # Create main rect
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.midtop = ai_game.ship.rect.midtop

        # Create glow surface
        self.glow_surface = pygame.Surface((self.glow_width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.glow_surface, (255, 100, 100, 30),
                        self.glow_surface.get_rect(),
                        border_radius=2)

        # Position tracking
        self.y = float(self.rect.y)

    def update(self):
        """Move the laser up the screen."""
        self.y -= self.settings.bullet_speed
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the laser with glow effect."""
        # Draw glow first
        glow_rect = self.glow_surface.get_rect(center=self.rect.center)
        self.screen.blit(self.glow_surface, glow_rect)

        # Draw core laser
        pygame.draw.rect(self.screen, self.core_color, self.rect,
                        border_radius=1)

        # Draw trailing particles
        for i in range(3):
            trail_y = self.rect.bottom + i * 5
            pygame.draw.circle(self.screen, self.trail_color,
                              (self.rect.centerx, trail_y),
                              radius=2 - i)
