"""Preserved consumer regressions against shipping native adapters."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
sys.path.insert(0, str(ROOT / 'tests/native_start'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))

if __name__ == '__main__':
    from case_inventory import execute
    execute(ROOT, 'tests/shared-regression-cases.json',
            '5a70e9018b908a4957db875df2900c661f5a1548d0d0c3a4eec2db6220df890a',
            ['test_central_exact_versions', 'test_hosted_bundle_content', 'test_hosted_frontend_update',
             'test_pending_activation', 'test_private_files', 'test_selected_shell_composition'])
