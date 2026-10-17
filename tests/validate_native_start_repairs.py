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
            '617e1fa50b9f0f8d990d110511f1ef07225d19b3b2180d862e9f41778eede247',
            ['test_central_exact_versions', 'test_hosted_bundle_content', 'test_hosted_frontend_update',
             'test_pending_activation', 'test_private_files', 'test_selected_shell_composition'])
