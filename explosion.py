import pygame
from pygame.sprite import Sprite
import random

class Explosion(Sprite):
    """Explosion animation class"""
    
    def __init__(self, center, size=30):
        super().__init__()
        self.size = size
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # ms between frames
        
        # Required Sprite attributes
        self.image = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        
        # Create particles
        self.particles = []
        for _ in range(20):
            particle = {
                "pos": [self.rect.centerx, self.rect.centery],
                "vel": [random.uniform(-3, 3), random.uniform(-3, 3)],
                "color": (random.randint(200, 255), random.randint(50, 150), 0),
                "size": random.randint(2, 4)
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
                p["vel"][0] *= 0.9
                p["vel"][1] *= 0.9
                p["size"] = max(0, p["size"] - 0.5)
                
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