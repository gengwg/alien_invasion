"""Resolve resource paths relative to the project directory.

Asset loading must not depend on the caller's current working directory,
so all images, sounds, and the high-score file are located relative to
this module's location.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HIGH_SCORE_FILE = os.path.join(BASE_DIR, 'high_score.txt')


def resource_path(*parts):
    """Return an absolute path to a resource inside the project directory."""
    return os.path.join(BASE_DIR, *parts)
