from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(label: str, text: str, phrases: tuple[str, ...]) -> None:
    normalized = " ".join(text.split())
    missing = [phrase for phrase in phrases if " ".join(phrase.split()) not in normalized]
    if missing:
        raise AssertionError(f"{label} is missing required test policy: {missing}")


def main() -> int:
    aggregate = (ROOT / "scripts/Test-ProgramKit.ps1").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release_guide = (ROOT / "docs/releasing-0.10.0.md").read_text(encoding="utf-8")
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    require(
        "aggregate script",
        aggregate,
        (
            "[ValidateSet('Development', 'Release')]",
            "[string]$Suite = 'Development'",
            "PROGRAM_KIT_RELEASE_VALIDATION_APPROVAL_REQUIRED",
            "PROGRAM_KIT_RELEASE_VALIDATION_ISE_UNSUPPORTED",
            "$Host.Name -eq 'Windows PowerShell ISE Host'",
            "standalone Windows PowerShell console",
            "$Suite -eq 'Release' -and -not $Approved",
            "validate_test_suites.py",
            "validate_ui_browser.py",
            "build_release.py",
            "validate_public_upgrade.py",
            "Test-LocalInstall.ps1",
            "verify_legacy_programkit_nuget.py",
            "write_release_receipt.py",
            "release-validation-$version.log",
            "Start-Transcript",
            "[Console]::OutputEncoding = $utf8NoBom",
            "$env:PYTHONIOENCODING = 'utf-8'",
            "[Console]::OutputEncoding = $previousConsoleOutputEncoding",
            "Program Kit complete deterministic Release suite passed.",
        ),
    )
    if any(name in aggregate for name in ("Test-LiveBootstrap.ps1", "run_bootstrap_acceptance.py", "Start-IntakeSession.ps1")):
        raise AssertionError("The deterministic aggregate must never launch paid Codex workers.")

    development_match = re.search(
        r"\$developmentValidators\s*=\s*@\((.*?)\)\s*\$releaseOnlyValidators",
        aggregate,
        re.DOTALL,
    )
    if development_match is None:
        raise AssertionError("Could not locate the bounded Development validator list.")
    development = development_match.group(1)
    for forbidden in (
        "validate_governance_state.py",
        "validate_local_upgrade.py",
        "validate_lifecycle_profiles.py",
        "validate_ui_browser.py",
        "validate_release_install.py",
    ):
        if forbidden in development:
            raise AssertionError(f"Development suite regained release-only validator {forbidden}.")

    require(
        "contributor instructions",
        agents,
        (
            "Test-ProgramKit.ps1 -Suite Release -Approved",
            "do not start the complete Release suite from a Codex Desktop task",
            "Only an explicitly authorized live-acceptance v2 phase starts automated coding-agent sessions",
            "Never launch its interactive mode from an agent, CI, a deterministic suite, or an unattended hook",
            "Never recreate a boolean `-Approved` path",
            "a different commit SHA alone does not require another local Release run or a new local receipt",
            "Shipped content and its build inputs are unchanged",
            "CI is green for the latest candidate commit",
            "Preserve the original receipt unchanged",
            "Live-acceptance receipt consumption retains its exact source",
            "The separate failed stable-release recovery procedure is unchanged",
        ),
    )
    for document, label in ((readme, "README"), (release_guide, "release guide")):
        require(
            label,
            document,
            (
                "Test-ProgramKit.ps1 -Suite Release -Approved",
                "chromium,webkit",
            ),
        )
    for workflow, label in ((ci, "CI"), (release, "Release workflow")):
        if "python tests/validate_test_suites.py" not in workflow:
            raise AssertionError(f"{label} does not enforce the test-tier contract.")

    require(
        "release evidence reuse",
        release_guide,
        (
            "../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes",
            "Preserve the original receipt unchanged",
            "The tagged Release workflow still runs in full",
        ),
    )

    print("Development, release, and paid live test boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
