"""Bounded operational journeys; no agent, database, native build or browser runs.

Each family has a deliberately narrow claim. Cheap regression cases remain in
their focused modules; this entrypoint selects only the representative journeys.
Native installation journeys use the prepared Specify interpreter. Preview upgrade
exercises actual owned toolkit replacement and rollback, not 0.x workflow translation.
Knowledge and optional scaffold journeys keep their own selected prerequisites.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPROVALS = ('--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved')


def sync(root: Path, *arguments: str, environment=None):
    return subprocess.run([sys.executable,
        str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
        '--target', str(root), *arguments], cwd=ROOT, env=environment,
        capture_output=True, text=True, encoding='utf-8', timeout=45)


def snapshot(root: Path):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class ScaffoldJourney(unittest.TestCase):
    def test_generation_validation_and_rejected_selection_preserve_authored_files(self):
        with tempfile.TemporaryDirectory(prefix='pk scaffold space ') as directory:
            root = Path(directory)
            authored = root / 'consumer-notes.txt'
            authored.write_bytes(b'Consumer-owned design decisions.\n')
            before = snapshot(root)
            rejected = sync(root)
            self.assertEqual(3, rejected.returncode, rejected.stdout + rejected.stderr)
            self.assertEqual(before, snapshot(root))
            installed = sync(root, *APPROVALS, '--web-profile', 'none')
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            state = json.loads((root / 'config/program-kit/managed.json').read_text())
            self.assertEqual('none', state['selections']['web'])
            self.assertTrue((root / 'scripts/Build.ps1').is_file())
            self.assertTrue((root / 'Directory.Build.props').is_file())
            self.assertEqual(b'Consumer-owned design decisions.\n', authored.read_bytes())
            # Execute the emitted lightweight drift contract, without claiming
            # that the generated composition compiles or starts successfully.
            checked = sync(root, '--profile-selected', '--web-profile', 'none', '--check')
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            shell = json.loads((root / 'config/program-kit/web-profile.shells.json').read_text())
            self.assertEqual({}, shell['CShells']['Shells']['default']['Features'])
            emitted = subprocess.run([sys.executable, '-I', '-c',
                'import sys,json; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/"scripts")); '
                'import shell_composition; print(json.dumps(shell_composition.compose(Path.cwd())))'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(0, emitted.returncode, emitted.stdout + emitted.stderr)
            self.assertEqual({}, json.loads(emitted.stdout)['CShells']['Shells']['default']['Features'])


class UpgradeJourney(unittest.TestCase):
    def test_profile_upgrade_rollback_retry_and_managed_conflict(self):
        with tempfile.TemporaryDirectory(prefix='pk upgrade space ') as directory:
            root = Path(directory)
            authored = root / 'consumer-notes.txt'
            authored.write_bytes(b'Keep consumer-authored content.\n')
            result = sync(root, *APPROVALS, '--web-profile', 'bff-cookie')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            # BffCookie 0.3.7 requires these feature activations, independently
            # of whether the corresponding packages are already restored.
            required = {'Orbyss.Foundation.Authentication', 'Orbyss.Foundation.WebDefaults',
                        'Orbyss.Foundation.Json.AspNetCore'}
            emitted_profile = json.loads((root / 'config/program-kit/web-profile.shells.json').read_text())
            features = emitted_profile['CShells']['Shells']['default']['Features']
            self.assertTrue(required <= features.keys())
            composed = subprocess.run([sys.executable, '-I', '-c',
                'import sys,json; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/"scripts")); '
                'import shell_composition; print(json.dumps(shell_composition.compose(Path.cwd())))'],
                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(0, composed.returncode, composed.stdout + composed.stderr)
            composed_features = json.loads(composed.stdout)['CShells']['Shells']['default']['Features']
            self.assertTrue(required <= composed_features.keys())
            self.assertIn('Orbyss.Foundation.Authentication.BffCookie', composed_features)
            before = snapshot(root)
            environment = dict(os.environ, PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION='2')
            interrupted = sync(root, *APPROVALS, '--web-profile', 'spa-pkce', environment=environment)
            self.assertEqual(2, interrupted.returncode, interrupted.stdout + interrupted.stderr)
            self.assertIn('rolled back', interrupted.stderr)
            self.assertEqual(before, snapshot(root))
            retry = sync(root, *APPROVALS, '--web-profile', 'spa-pkce')
            self.assertEqual(0, retry.returncode, retry.stdout + retry.stderr)
            self.assertFalse((root / 'tools/program-kit/web/bff-session.ts').exists())
            self.assertTrue((root / 'tools/program-kit/web/spa-session.ts').is_file())
            self.assertEqual(b'Keep consumer-authored content.\n', authored.read_bytes())
            managed = root / 'config/program-kit/spa-pkce.json'
            managed.write_bytes(managed.read_bytes() + b'\nConsumer customization\n')
            before = snapshot(root)
            conflict = sync(root, *APPROVALS, '--web-profile', 'bff-cookie')
            self.assertEqual(2, conflict.returncode, conflict.stdout + conflict.stderr)
            self.assertEqual(before, snapshot(root))


CASES = {
    'phases': ['validate_native_phases.NativePhaseTests'],
    'knowledge': ['validate_native_phases.KnowledgeTests'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True, choices=['phases', 'knowledge', 'founding', 'upgrade', 'scaffold'])
    args = parser.parse_args()
    scratch = ROOT / 'artifacts/t'
    scratch.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(scratch)
    started = time.monotonic()
    try:
        if args.family == 'founding':
            from validate_product_intake import scenario
            scenario(source_payload=True)
            success = True
        elif args.family == 'upgrade':
            from validate_preview_distribution import native_refresh
            native_refresh()
            success = True
        elif args.family == 'scaffold':
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(ScaffoldJourney)
            success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
        else:
            suite = unittest.defaultTestLoader.loadTestsFromNames(CASES[args.family])
            success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    finally:
        print(json.dumps({'family': args.family, 'elapsedSeconds': round(time.monotonic() - started, 3),
            'scope': 'Representative mechanics; fictional artifacts establish no agent or human acceptance.'}), flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
