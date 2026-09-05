from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def run(command: list[str], repository: Path) -> int:
    result = subprocess.run(command, cwd=repository, check=False)
    return result.returncode


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(
        description="Run the deterministic lifecycle and artifact-ownership implementation preflight."
    )
    parser.add_argument("--repository", default=".")
    parser.add_argument("--feature-dir", required=True)
    args = parser.parse_args()
    repository = Path(args.repository).resolve()
    feature_dir = Path(args.feature_dir)
    if not feature_dir.is_absolute():
        feature_dir = (repository / feature_dir).resolve()
    try:
        feature_dir.relative_to(repository)
    except ValueError:
        print("PKI001 feature directory must stay inside the repository.", file=sys.stderr)
        return 2
    scripts = Path(__file__).resolve().parent
    lifecycle = run(
        [
            sys.executable,
            str(scripts / "lifecycle_state.py"),
            "--repository",
            str(repository),
            "--feature-dir",
            str(feature_dir),
            "verify-before-implement",
        ],
        repository,
    )
    if lifecycle != 0:
        return lifecycle
    manifest = feature_dir / "artifact-ownership.json"
    plan = feature_dir / "plan.md"
    tasks = feature_dir / "tasks.md"
    ownership = run(
        [
            sys.executable,
            str(scripts / "artifact_ownership.py"),
            "--manifest",
            str(manifest),
            "--plan",
            str(plan),
            "--tasks",
            str(tasks),
        ],
        repository,
    )
    if ownership != 0:
        return ownership
    print("implementation preflight lifecycle and artifact ownership are coherent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
