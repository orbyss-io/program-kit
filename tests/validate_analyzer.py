from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    project = root / "tests/analyzer-probe/AnalyzerProbe.csproj"
    restore = subprocess.run(
        ["dotnet", "restore", str(project), "--locked-mode", "--nologo"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if restore.returncode != 0:
        raise AssertionError(f"The analyzer probe did not restore in locked mode.\n{restore.stdout}{restore.stderr}")

    result = subprocess.run(
        ["dotnet", "build", str(project), "--no-restore", "--nologo"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode == 0:
        raise AssertionError("The invalid analyzer probe unexpectedly compiled.")
    for rule_id in ("PK1003", "PK1004", "PK1005"):
        if rule_id not in output:
            raise AssertionError(f"The analyzer probe did not report {rule_id}.\n{output}")

    print("Program Kit C# structure and documentation analyzers passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
