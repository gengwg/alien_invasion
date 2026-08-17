"""Line coverage for the game modules, using only the standard library.

Usage:
    python tests/coverage_report.py
"""

import os
import sys
import trace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pytest

MODULES = ["alien_invasion.py", "profiles.py", "profile_panel.py",
           "game_stats.py", "scoreboard.py", "settings.py", "ship.py",
           "bullet.py", "alien.py", "star.py", "explosion.py", "button.py",
           "paths.py"]


def main():
    os.chdir(ROOT)
    tracer = trace.Trace(count=1, trace=0,
                         ignoredirs=[sys.prefix, sys.exec_prefix])
    tracer.runfunc(pytest.main, ["tests/", "-q"])

    executed = {}
    for (filename, lineno), _count in tracer.results().counts.items():
        executed.setdefault(os.path.abspath(filename), set()).add(lineno)

    covered = total = 0
    for module in MODULES:
        path = os.path.join(ROOT, module)
        lines = set(trace._find_executable_linenos(path))
        hit = lines & executed.get(path, set())
        covered += len(hit)
        total += len(lines)
        missing = sorted(n for n in lines - hit if n)
        print(f"{module:20s} {100.0 * len(hit) / len(lines):5.1f}% "
              f"({len(hit)}/{len(lines)})  missing: {missing}")
    print(f"{'TOTAL':20s} {100.0 * covered / total:5.1f}% ({covered}/{total})")


if __name__ == "__main__":
    main()
