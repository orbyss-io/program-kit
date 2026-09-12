"""Exercise actual Spec Kit registration/removal with consumer-edit protection."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from specify_cli.extensions import ExtensionManager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import retired_sync_integration as retired


class RetirementTests(unittest.TestCase):
    def test_real_registration_edit_guard_removal_and_reinstall(self):
        with tempfile.TemporaryDirectory(prefix='program-kit-retirement-') as value:
            base = Path(value)
            root = base / 'consumer'
            (root / '.specify').mkdir(parents=True)
            (root / '.agents/skills').mkdir(parents=True)
            (root / '.specify/init-options.json').write_text(json.dumps({'ai':'codex','ai_skills':True}))
            source = base / 'previous'
            (source / 'commands').mkdir(parents=True)
            (source / 'extension.yml').write_text('''schema_version: "1.0"
extension:
  id: "program-kit-dotnet"
  name: "Previous .NET command test fixture"
  version: "0.10.0"
  description: "Synthetic previous public command for registrar integration testing."
requires:
  speckit_version: ">=1.0.1,<2.0.0"
provides:
  commands:
    - name: "speckit.program-kit-dotnet.sync"
      file: "commands/sync.md"
      description: "Synchronize previous baseline."
''', encoding='utf-8')
            (source / 'commands/sync.md').write_text('---\ndescription: Synchronize previous baseline.\n---\n\nPrevious test command.\n')
            manager = ExtensionManager(root)
            manager.install_from_directory(source, '1.0.1')
            skill = root / '.agents/skills' / retired.SKILL / 'SKILL.md'
            original = skill.read_bytes()
            retired.preflight(root)
            skill.write_bytes(original + b'\nConsumer customization.\n')
            with self.assertRaisesRegex(ValueError, 'consumer edits'):
                retired.preflight(root)
            self.assertTrue(skill.read_bytes().endswith(b'Consumer customization.\n'))
            skill.write_bytes(original)
            extra = skill.parent / 'consumer.txt'
            extra.write_text('Keep this file')
            with self.assertRaisesRegex(ValueError, 'consumer files'):
                retired.preflight(root)
            extra.unlink()
            retired.preflight(root)
            manager.install_from_directory(ROOT / 'extensions/program-kit-dotnet', '1.0.1', force=True)
            retired.verify_removed(root)
            self.assertFalse(skill.exists())
            for force in (False, True):
                manager.install_from_directory(ROOT / 'extensions/program-kit-governance', '1.0.1', force=force)
            self.assertTrue((root / '.agents/skills/speckit-program-kit-governance-sync/SKILL.md').is_file())
            retired.verify_removed(root)


if __name__ == '__main__':
    unittest.main()
