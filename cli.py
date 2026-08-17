"""Command-line interface: window mode, player selection and player admin."""

import argparse
import re

from profiles import DIFFICULTIES, ProfileError

DEFAULT_WINDOW = "1200x800"

_SIZE_RE = re.compile(r"^(\d{3,5})x(\d{3,5})$")


def window_size(text):
    """Parse a 'WIDTHxHEIGHT' option value into a (width, height) tuple."""
    match = _SIZE_RE.match(str(text).strip().lower())
    if not match:
        raise argparse.ArgumentTypeError(
            f"expected a size like {DEFAULT_WINDOW}, got '{text}'")
    return int(match.group(1)), int(match.group(2))


def build_parser():
    """Build the argument parser for the game."""
    parser = argparse.ArgumentParser(
        prog="alien_invasion.py", description="Alien Invasion")
    parser.add_argument(
        '--windowed', nargs='?', const=DEFAULT_WINDOW, type=window_size,
        metavar='WxH', help=f"run in a window (default {DEFAULT_WINDOW})")
    parser.add_argument(
        '--player', metavar='NAME',
        help="play as NAME, creating the player if needed")
    parser.add_argument(
        '--difficulty', choices=DIFFICULTIES,
        help="set the player's difficulty before starting")
    parser.add_argument(
        '--list-players', action='store_true',
        help="print the saved players and exit")
    parser.add_argument(
        '--delete-player', metavar='NAME', help="delete a player and exit")
    return parser


def parse_args(argv=None):
    """Parse command-line arguments (argv defaults to sys.argv[1:])."""
    return build_parser().parse_args(argv)


def run_admin_commands(options, store):
    """Run the options that manage players instead of playing.

    Returns an exit code when the game should not start, else None.
    """
    if options.list_players:
        _print_players(store)
        return 0
    if options.delete_player:
        try:
            store.delete(options.delete_player)
        except ProfileError as e:
            print(f"error: {e}")
            return 1
        print(f"Deleted {options.delete_player}.")
        return 0
    return None


def apply_player_options(options, store):
    """Select/create the requested player and difficulty before playing."""
    if options.player:
        try:
            store.select(options.player)
        except ProfileError:
            store.create(options.player)
    if options.difficulty:
        store.set_difficulty(options.difficulty)


def _print_players(store):
    """Print one line per player, plus who is active."""
    names = store.names()
    if not names:
        print("No players yet.")
        return
    print(f"{'Player':14s}{'High':>10s}{'Level':>7s}{'Games':>7s}  Difficulty")
    for name in names:
        stats = store.stats_for(name)
        marker = '*' if name == store.active else ' '
        print(f"{marker}{name:13s}{stats['high_score']:>10,}"
              f"{stats['best_level']:>7}{stats['games_played']:>7}"
              f"  {stats['difficulty']}")
    print("\n* active player")
