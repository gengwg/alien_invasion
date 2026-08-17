"""Small helpers shared by the test modules."""

import pygame


def start_game(ai):
    """Start a game the way clicking the Play button does."""
    ai._check_play_button(ai.play_button.rect.center)


def press(ai, key, unicode=""):
    """Send a single KEYDOWN through the real key handler."""
    ai._check_keydown_events(pygame.event.Event(pygame.KEYDOWN, key=key,
                                                unicode=unicode))


def type_name(ai, name):
    """Type a name into the open name-entry prompt, character by character."""
    for char in name:
        press(ai, ord(char) if len(char) == 1 else 0, unicode=char)
