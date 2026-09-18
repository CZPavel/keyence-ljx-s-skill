"""Run a repository helper from the activated thin Keyence skill."""
import argparse
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = {
    "skill_lookup": ROOT / "tools" / "skill_lookup.py",
    "head_geometry": ROOT / "tools" / "head_geometry.py",
    "corpus_lookup": ROOT / "tools" / "corpus_lookup.py",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=TOOLS)
    args, remaining = parser.parse_known_args()
    target = TOOLS[args.tool]
    if not target.is_file():
        raise SystemExit(f"Canonical helper is missing from this skill checkout: {target}")
    sys.argv = [str(target), *remaining]
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
