"""Preserved consumer regressions against shipping native adapters."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(ROOT / 'tests/native_start'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend', action='store_true', help='Run the real generated Vite build/update fixtures')
    args = parser.parse_args()
    modules = ['test_hosted_frontend_update'] if args.frontend else [
        'test_central_exact_versions', 'test_hosted_bundle_content',
        'test_pending_activation', 'test_private_files', 'test_selected_shell_composition']
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
