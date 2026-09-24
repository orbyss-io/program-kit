from __future__ import annotations

import re
import ast
import json
import sys
import yaml
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
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    release_guide = (ROOT / f"docs/releasing-{version}.md").read_text(encoding="utf-8")
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
            "scripts/run_validation.py",
            "release-validation-$version.log",
            "Start-Transcript",
            "[Console]::OutputEncoding = $utf8NoBom",
            "$env:PYTHONIOENCODING = 'utf-8'",
            "[Console]::OutputEncoding = $previousConsoleOutputEncoding",
        ),
    )
    if any(name in aggregate for name in ("Test-LiveBootstrap.ps1", "run_bootstrap_acceptance.py", "Start-IntakeSession.ps1")):
        raise AssertionError("The deterministic aggregate must never launch paid Codex workers.")

    inventory = json.loads((ROOT / 'tests/validation-inventory.json').read_text())['checks']
    # Catch stale late/post-publication expectations during the cheap source gate.
    expected_hooks = set(yaml.safe_load((ROOT / 'extensions/program-kit-governance/extension.yml').read_text())['hooks'])
    for filename in ('validate_components.py', 'validate_release_install.py', 'validate_public_install.py', 'validate_public_upgrade.py'):
        tree = ast.parse((ROOT / 'tests' / filename).read_text(encoding='utf-8'))
        declared = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == 'EXPECTED_HOOKS' for target in node.targets))
        if declared != expected_hooks:
            raise AssertionError(filename + ' has obsolete installation hook expectations')
    development = [c['id'] + '.py' for c in inventory if c['group'] == 'development']
    if 'validate_governance_state.py' not in development:
        raise AssertionError('Development must exercise governance behavior')
    for forbidden in ('validate_local_upgrade.py', 'validate_lifecycle_profiles.py', 'validate_ui_browser.py', 'validate_release_install.py'):
        if forbidden in development:
            raise AssertionError('Development includes a Release-only check: ' + forbidden)
    ids = [c['id'] for c in inventory]
    if len(set(ids)) != len(ids):
        raise AssertionError('Duplicate validation ID')
    for check in inventory:
        if not set(check['needs']) <= set(ids):
            raise AssertionError('Unknown check prerequisite')
        if check['command'][0] == '{python}' and not (ROOT / check['command'][1]).is_file():
            raise AssertionError('Missing validator: ' + check['id'])
    for required in ('validate_bootstrap_runtime', 'validate_published_forms_browser', 'source-install', 'public-availability', 'legacy-public'):
        if required not in ids:
            raise AssertionError('Missing integration gate: ' + required)

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
            "must not alter release build, packaging or publication behavior",
            "nothing was published from the failed candidate",
            "not a product failure",
            "If any condition cannot be established, obtain fresh local Release evidence",
            "Obtain or confirm the user's approval for the exact corrected commit and same stable tag",
            "evidence reuse never authorizes moving a tag by itself",
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
        definition = yaml.safe_load(workflow)
        steps = next(iter(definition['jobs'].values()))['steps']
        invocations = [s for s in steps if 'scripts/run_validation.py --suite Release --approved' in s.get('run', '')]
        if len(invocations) != 1:
            raise AssertionError(label + ' must run the shared inventory exactly once')
        if 'global-json-file: extensions/program-kit-dotnet/templates/dotnet/files/global.json' not in workflow:
            raise AssertionError(label + ' lacks the pinned SDK')
        if not any(s.get('if') == 'always()' and 'upload-artifact@' in s.get('uses', '') for s in steps):
            raise AssertionError(label + ' must preserve failed validation evidence')
        if label == 'Release workflow':
            if '--receipt' not in invocations[0]['run']:
                raise AssertionError('Tagged Release requires an executed-check receipt')
            publish = next(i for i, s in enumerate(steps) if s.get('name') == 'Publish GitHub release')
            if steps.index(invocations[0]) >= publish:
                raise AssertionError('Validation must precede publication')

    require(
        "release evidence reuse",
        release_guide,
        (
            "../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes",
            "Preserve the original receipt unchanged",
            "The tagged Release workflow still runs in full",
            "nothing was published from the failed candidate",
            "Exact corrected-commit and same-tag approval is still required",
            "If any reuse condition is unproven, obtain fresh local Release evidence",
        ),
    )

    print("Development, release, and paid live test boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
