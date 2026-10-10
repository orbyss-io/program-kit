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


def shared_inventory_invocation(steps: list[dict], label: str) -> dict:
    marker='scripts/run_validation.py --suite' if label=='Release workflow' else 'scripts/run_validation.py'
    invocations=[step for step in steps if marker in step.get('run','')]
    if len(invocations)!=1:
        raise AssertionError(label+' must run the shared inventory exactly once')
    return invocations[0]


def validate_ci_selection(step: dict) -> None:
    """Verify the executable fixed-argv CI route, preserving default and automatic coverage."""
    import os
    import subprocess
    from unittest.mock import patch
    environment=step.get('env',{})
    for name,expected in (('EVENT_NAME','${{ github.event_name }}'),
                          ('BASE_SHA','${{ github.event.pull_request.base.sha }}'),
                          ('VALIDATION_SELECTION','${{ inputs.validation }}')):
        if environment.get(name)!=expected:
            raise AssertionError('CI selection must obtain '+name+' as environment data')
    lines=step.get('run','').splitlines()
    if not lines or lines[0]!="python - <<'PY'" or lines[-1]!='PY':
        raise AssertionError('CI selection must use the reviewed Python argument-array route')
    routing='\n'.join(lines[1:-1])
    command=['python','scripts/run_validation.py']
    common=['--workers','4','--engines=chromium,firefox,webkit']
    routes=[('workflow_dispatch',None,['--suite','PullRequest']),
            ('workflow_dispatch','',['--suite','PullRequest']),
            ('workflow_dispatch','full',['--suite','PullRequest']),
            ('workflow_dispatch','qualify_reusable_foundations',['--check','qualify_reusable_foundations']),
            ('pull_request','qualify_reusable_foundations',['--suite','PullRequest','--changed-from','base-commit']),
            ('push','qualify_reusable_foundations',['--suite','Development']),
            ('push','unknown',['--suite','Development'])]
    for event,selection,arguments in routes:
        values={'EVENT_NAME':event,'BASE_SHA':'base-commit'}
        if selection is not None: values['VALIDATION_SELECTION']=selection
        with patch.dict(os.environ,values,clear=True),patch.object(subprocess,'run') as run:
            exec(routing,{})
            if run.call_count!=1 or run.call_args.args!=(command+arguments+common,) or run.call_args.kwargs!={'check':True}:
                raise AssertionError('CI selection changed shared coverage or execution for '+event)
    for selection in ('unknown','qualify_reusable_foundations; echo injected','--suite Release --receipt'):
        with patch.dict(os.environ,{'EVENT_NAME':'workflow_dispatch','VALIDATION_SELECTION':selection},clear=True), \
                patch.object(subprocess,'run') as run:
            try: exec(routing,{})
            except SystemExit as error:
                if error.code in (None,0): raise AssertionError('CI selection must fail unknown manual values')
            else: raise AssertionError('CI selection must reject unknown manual values')
            if run.called: raise AssertionError('CI selection executed an unknown manual value')


def main() -> int:
    aggregate = (ROOT / "scripts/Test-ProgramKit.ps1").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    release_guide = (ROOT / 'docs/releasing.md').read_text(encoding="utf-8")
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

    sys.path.insert(0, str(ROOT / 'scripts'))
    from run_validation import require_release_authority
    for marker in ('CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CODEX_INTERNAL_ORIGINATOR_OVERRIDE'):
        environment = {marker: 'fixture'}
        try:
            require_release_authority('Release', True, False, environment, 'nt')
        except ValueError as error:
            assert 'user-owned terminal' in str(error)
        else:
            raise AssertionError('Default Codex task restriction must remain effective')
        require_release_authority('Release', True, True, environment, 'nt')
        try:
            require_release_authority('Release', False, True, environment, 'nt')
        except ValueError as error:
            assert 'publication approval' in str(error)
        else:
            raise AssertionError('Task opt-in must not authorize publication by itself')
    require_release_authority('Release', True, False, {}, 'nt')
    require_release_authority('Release', True, False, {}, 'posix')
    require_release_authority('Development', False, False, {'CODEX_THREAD_ID': 'fixture'}, 'nt')
    try:
        require_release_authority('Development', True, True, {}, 'nt')
    except ValueError as error:
        assert 'requires Release' in str(error)
    else:
        raise AssertionError('Release task opt-in must not apply to other suites')
    require('aggregate task opt-in', aggregate,
            ('[switch]$AuthorizedCodexTask', "if ($AuthorizedCodexTask)", '--authorized-codex-task'))
    runner = (ROOT / 'scripts/run_validation.py').read_text(encoding='utf-8')
    require('recorded task authority', runner,
            ("'authorizedCodexTask': args.authorized_codex_task", 'require_release_authority(args.suite'))

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
        invocation = shared_inventory_invocation(steps, label)
        if 'global-json-file: extensions/program-kit-dotnet/templates/dotnet/files/global.json' not in workflow:
            raise AssertionError(label + ' lacks the pinned SDK')
        if not any(s.get('if') == 'always()' and 'upload-artifact@' in s.get('uses', '') for s in steps):
            raise AssertionError(label + ' must preserve failed validation evidence')
        if label == 'Release workflow':
            if '--receipt' not in invocation['run']:
                raise AssertionError('Tagged Release requires an executed-check receipt')
            publish = next(i for i, s in enumerate(steps) if s.get('name') == 'Publish GitHub release')
            if steps.index(invocation) >= publish:
                raise AssertionError('Validation must precede publication')
        else:
            validate_ci_selection(invocation)

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
