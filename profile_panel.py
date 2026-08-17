"""Idle-screen panel for player management: current player, top scores, hints."""

import pygame.font

from profiles import MAX_NAME_LENGTH

TEXT_COLOR = (220, 220, 220)
HINT_COLOR = (140, 140, 170)
MESSAGE_COLOR = (255, 220, 100)
TITLE_COLOR = (100, 255, 100)


class ProfilePanel:
    """Draw profile information under the Play button while the game is idle."""

    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.bg_color = ai_game.settings.bg_color

        self.font = pygame.font.SysFont(None, 32)
        self.hint_font = pygame.font.SysFont(None, 26)

    def draw(self):
        """Draw the panel, centered below the Play button."""
        top = self.ai_game.play_button.rect.bottom + 40

        # The active player's name is already in the scoreboard, so the panel
        # only shows what the player can do about it.
        if self.ai_game.name_input is None:
            top = self._draw_line(
                "N: new player    TAB: switch player    DEL: delete player",
                self.hint_font, HINT_COLOR, top)
        else:
            top = self._draw_line(
                f"New player name: {self.ai_game.name_input}_",
                self.font, TEXT_COLOR, top)
            top = self._draw_line(
                f"Enter: confirm    Esc: cancel    (max {MAX_NAME_LENGTH} chars)",
                self.hint_font, HINT_COLOR, top)

        if self.ai_game.profile_message:
            top = self._draw_line(self.ai_game.profile_message, self.hint_font,
                                  MESSAGE_COLOR, top)

        leaderboard = self.ai_game.profiles.leaderboard()
        if leaderboard:
            top = self._draw_line("- Top Pilots -", self.hint_font,
                                  TITLE_COLOR, top + 10)
            for rank, (name, high_score) in enumerate(leaderboard, start=1):
                top = self._draw_line(f"{rank}. {name} - {high_score:,}",
                                      self.hint_font, TEXT_COLOR, top)

    def _draw_line(self, text, font, color, top):
        """Blit one centered line and return the top of the next line."""
        image = font.render(text, True, color, self.bg_color)
        rect = image.get_rect()
        rect.centerx = self.screen_rect.centerx
        rect.top = top
        self.screen.blit(image, rect)
        return rect.bottom + 6
