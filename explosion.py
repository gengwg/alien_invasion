import pygame
from pygame.sprite import Sprite
import random

class Explosion(Sprite):
    """Explosion animation class with different sizes"""
    
    def __init__(self, center, explosion_type='alien'):
        super().__init__()
        self.explosion_type = explosion_type
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # ms between frames
        
        # Configure based on explosion type
        if self.explosion_type == 'ship':
            self.size = 60
            self.num_particles = 50
            self.colors = [
                (255, 100, 100),  # Red
                (255, 150, 50),    # Orange
                (255, 255, 150)    # Yellow
            ]
        else:  # Default/alien explosion
            self.size = 30
            self.num_particles = 30
            self.colors = [
                (255, 150, 0),    # Orange
                (200, 100, 0),     # Dark orange
                (255, 200, 100)    # Light yellow
            ]

        # Required Sprite attributes
        self.image = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        
        # Create particles
        self.particles = []
        for _ in range(self.num_particles):
            particle = {
                "pos": [self.rect.centerx, self.rect.centery],
                "vel": [
                    random.uniform(-5, 5) * (2 if self.explosion_type == 'ship' else 1),
                    random.uniform(-5, 5) * (2 if self.explosion_type == 'ship' else 1)
                ],
                "color": random.choice(self.colors),
                "size": random.randint(
                    3, 6) if self.explosion_type == 'ship' else random.randint(2, 4)
            }
            self.particles.append(particle)

    def update(self):
        """Update explosion particles"""
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            
            for p in self.particles:
                p["pos"][0] += p["vel"][0]
                p["pos"][1] += p["vel"][1]
                p["vel"][0] *= 0.85 if self.explosion_type == 'ship' else 0.9
                p["vel"][1] *= 0.85 if self.explosion_type == 'ship' else 0.9
                p["size"] = max(0, p["size"] - (
                    0.5 if self.explosion_type == 'ship' else 0.3))
                
            # Remove dead particles
            self.particles = [p for p in self.particles if p["size"] > 0]
            
        if not self.particles:
            self.kill()

    def draw(self, screen):
        """Draw explosion particles directly to screen"""
        for p in self.particles:
            pygame.draw.circle(screen, p["color"], 
                             (int(p["pos"][0]), int(p["pos"][1])), 
                             int(p["size"]))