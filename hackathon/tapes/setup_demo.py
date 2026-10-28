"""Set up the toy project for the video's live run: a copy of the bench's `unit-convert`
repository with a Token Factory ladder policy, committed to git.

    python hackathon/tapes/setup_demo.py                      # Nano-first policy (escalations)
    python hackathon/tapes/setup_demo.py --policy ladder      # the C-029 ladder
    python hackathon/tapes/setup_demo.py --dest <folder>

It writes `stepswitch.toml` (the chosen policy), `.stepswitch/local.toml` (the Token Factory
endpoint, from examples/tokenfactory/local.toml.example; the key stays in NEBIUS_API_KEY) and a
`.gitignore` for `.stepswitch/`, then prints the command to run. Standard library only.
"""

from __future__ import annotations

import argparse
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "bench" / "repos" / "unit-convert"
POLICIES = {
    "nano-first": ROOT / "bench" / "policies" / "tokenfactory-nano-first.toml",
    "ladder": ROOT / "bench" / "policies" / "tokenfactory-ladder.toml",
}
ENDPOINT = ROOT / "examples" / "tokenfactory" / "local.toml.example"
INSTRUCTION = (
    'Add temperatures to the unit converter: Celsius ("C"), Fahrenheit ("F") and Kelvin ("K"), '
    'as a new kind called "temperature". convert() must handle them (100 C is 212 F, and 0 C is '
    "273.15 K), and converting between a temperature and a length, mass or volume must still "
    "raise ValueError. tests/test_temperature.py describes the expected results."
)
GIT = [
    "git",
    "-c",
    "user.name=demo",
    "-c",
    "user.email=demo@example.invalid",
    "-c",
    "core.autocrlf=false",
]


def _writable(remove: object, path: str, _info: object) -> None:
    """Git marks its object files read-only, which Windows refuses to delete."""
    Path(path).chmod(stat.S_IWRITE)
    remove(path)  # type: ignore[operator]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--policy", choices=sorted(POLICIES), default="nano-first")
    parser.add_argument("--dest", type=Path, default=Path(tempfile.gettempdir()) / "unit-convert")
    args = parser.parse_args()

    dest: Path = args.dest.resolve()
    if dest.exists():
        shutil.rmtree(dest, onerror=_writable)
    shutil.copytree(REPO, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(POLICIES[args.policy], dest / "stepswitch.toml")
    (dest / ".stepswitch").mkdir()
    shutil.copyfile(ENDPOINT, dest / ".stepswitch" / "local.toml")
    (dest / ".gitignore").write_text(".stepswitch/\n__pycache__/\n", encoding="utf-8")
    for command in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "toy project"]):
        subprocess.run([*GIT, *command], cwd=dest, check=True)

    print(f"Toy project: {dest} (policy: {args.policy})")
    print("Then, with NEBIUS_API_KEY set, from that folder:")
    print(f"  uv run --project '{ROOT}' ssw run --allow-remote --budget-usd 0.3 '{INSTRUCTION}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
