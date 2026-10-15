"""Deterministic suite, qualification and publication ownership contracts."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from release_workflow_contracts import (shared_inventory_invocation, validate_ci_selection,
                                        validate_inventory, validate_workflows)

ROOT = Path(__file__).resolve().parents[1]


def main():
    validate_ci_selection()
    validate_inventory()
    validate_workflows()
    shell = shutil.which('pwsh') or shutil.which('powershell')
    if not shell:
        raise AssertionError('Suite policy requires PowerShell for retired entry point acceptance')
    for name, arguments in (('Test-ProgramKit.ps1', ['-Suite', 'Release', '-Approved']),
                            ('Invoke-LocalRelease.ps1', ['-PrepareOnly']),
                            ('Invoke-LocalRelease.ps1', ['-AuthorizedCodexTask'])):
        result = subprocess.run([shell, '-NoProfile', '-File', str(ROOT / 'scripts' / name), *arguments],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
        assert result.returncode != 0 and 'PROGRAM_KIT_LOCAL_RELEASE_RETIRED' in result.stdout + result.stderr
    print('Development, CI qualification, retired local commands and publication boundaries passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
