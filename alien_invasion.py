import sys

import pygame

from settings import Settings

class AlienInvasion:
    """overall class to manage game assets and behavior"""

    def __init__(self):
        """initialize the game and create game resources"""
        pygame.init()

        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )

        pygame.display.set_caption("Alien Invasion")

    def run_game(self):
        """start the main loop for the game"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            # redraw the screen during each passs through the loop.
            self.screen.fill(self.settings.bg_color)

            # make the most recently drawn screen visible.
            pygame.display.flip()


if __name__ == "__main__":
    ai = AlienInvasion()
    ai.run_game()
