# [file name]: bullet.py
import pygame
from pygame.sprite import Sprite

class Bullet(Sprite):
    """A class to manage laser beams fired from the ship."""

    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        # Laser colors and dimensions come from the game settings.
        self.core_color = self.settings.bullet_core_color
        self.trail_color = self.settings.bullet_trail_color

        self.width = self.settings.bullet_width
        self.height = self.settings.bullet_height
        self.glow_width = self.settings.bullet_glow_width

        # Create main rect
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.midtop = ai_game.ship.rect.midtop

        # Create glow surface
        self.glow_surface = pygame.Surface((self.glow_width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.glow_surface, self.settings.bullet_glow_color,
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
