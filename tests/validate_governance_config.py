"""Exercise installed governance configuration without third-party Python packages."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from validate_governance_state import write_installation


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "extensions/program-kit-governance/scripts/governance_state.py"
TEMPLATE = ROOT / "extensions/program-kit-governance/config/program-kit.template.yml"
CONFIGURATION = Path(".specify/extensions/program-kit-governance/program-kit-governance-config.yml")


def main() -> int:
    # -I ignores PYTHONPATH; -S excludes site packages, so the CLI cannot import PyYAML.
    isolated = [sys.executable, "-I", "-S"]
    probe = subprocess.run(
        [*isolated, "-c", "import importlib.util; assert importlib.util.find_spec('yaml') is None"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise AssertionError(f"Could not isolate PyYAML: {probe.stdout}\n{probe.stderr}")

    with tempfile.TemporaryDirectory(prefix="program-kit-governance-config-") as directory:
        project = Path(directory)
        write_installation(project, "0.3.1")
        configuration = project / CONFIGURATION
        shipped = TEMPLATE.read_bytes()
        configuration.write_bytes(shipped)
        command = [*isolated, str(SCRIPT), "validate-installation"]

        def validate(expected_code: int, diagnostic: str) -> None:
            result = subprocess.run(command, cwd=project, capture_output=True, text=True)
            output = result.stdout + result.stderr
            if result.returncode != expected_code or diagnostic not in output:
                raise AssertionError(
                    f"Expected exit {expected_code} and {diagnostic!r}, got exit {result.returncode}:\n{output}"
                )

        validate(0, "version-coherent: 0.3.1")
        for malformed in (
            'schema_version: "1.0"\n  stray: value\n',
            'schema_version: "1.0"\narchitecture:\n - decisions: wrong-indent\n',
            'schema_version: "1.0"\n- unexpected-sequence\n',
        ):
            configuration.write_text(malformed, encoding="utf-8")
            validate(1, "Invalid Program Kit configuration")

        configuration.write_bytes(shipped)
        local = configuration.with_name("program-kit-governance-config.local.yml")
        local.write_text("architecture:\n - decisions: wrong-indent\n", encoding="utf-8")
        validate(1, "Invalid Program Kit configuration")
        local.unlink()
        validate(0, "version-coherent: 0.3.1")

    print("Governance configuration works without PyYAML and rejects malformed input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
