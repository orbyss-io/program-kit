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
            '6c9a054350773f44646fd5c52adb0efdfaf517c94de7c4413e9b8a9631bb9f57',
            ['test_central_exact_versions', 'test_hosted_bundle_content', 'test_hosted_frontend_update',
             'test_pending_activation', 'test_private_files', 'test_selected_shell_composition'])
