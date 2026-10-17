"""Contributor pin authority follows shared package CI, without a device preflight."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import device_toolchain as policy


class PinAuthority(unittest.TestCase):
    def test_shared_workflow_supplies_exact_pin(self):
        with FixtureDirectory(prefix='shared-pin-') as directory:
            root = Path(directory)
            workflow = root / '.github/workflows/qualify-candidate.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('specify-cli==1.9.4\n')
            (workflow.parent / 'ci.yml').write_text('specify-cli==0.0.1\n')
            with patch.object(policy, 'is_contributor', return_value=True):
                expected, authority = policy.specify_requirement(root)
            self.assertEqual('1.9.4', expected)
            self.assertIn('qualify-candidate.yml', authority)

    def test_conflicting_shared_pins_are_rejected_without_probing_device(self):
        with FixtureDirectory(prefix='pin-authority-') as directory:
            root = Path(directory)
            workflow = root / '.github/workflows/qualify-candidate.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('specify-cli==1.2.0\nspecify-cli==1.3.0\n')
            with patch.object(policy, 'is_contributor', return_value=True), self.assertRaisesRegex(ValueError, 'one exact'):
                policy.specify_requirement(root)


if __name__ == '__main__':
    unittest.main()
