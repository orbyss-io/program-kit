"""Owned scratch lifecycle, deep Windows paths, and separate failure observations."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import owned_scratch as scratch


class OwnedScratchTests(unittest.TestCase):
    def test_failed_entry_preserves_integrity_error_and_residual_cleanup_observation(self):
        manager = scratch.owned_scratch(self.root, 'release-bundle')
        failure = ValueError('scratch identity changed during entry')
        with patch.object(manager, '_verify', side_effect=failure):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ValueError) as observed:
                manager.__enter__()
        self.assertIs(failure, observed.exception)
        self.assertTrue(manager.path.exists())
        self.assertFalse(failure.programkit_cleanup_failure['cleanupCompleted'])
        manager._remove()

    def test_deep_reconciliation_commits_and_rolls_back_without_shortening_ownership(self):
        import reconciliation
        relative = 'deploy/' + '/'.join(['identity-theme-' + 'x' * 28] * 5) + '/page.ftl'
        self.assertGreater(len(str(self.root / relative)), 300)
        actions = [{'kind': 'write', 'path': relative, 'content': b'original desired bytes'}]
        transaction = reconciliation.apply_plan(self.root, actions, b'{"version":1}')
        output = Path(scratch.filesystem_path(self.root / relative))
        self.assertEqual(b'original desired bytes', output.read_bytes())
        self.assertFalse((self.root / '.program-kit/transactions' / transaction).exists())
        with patch.dict(os.environ, {'PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION': '1'}):
            with self.assertRaisesRegex(OSError, 'Injected reconciliation interruption'):
                reconciliation.apply_plan(self.root, [{**actions[0], 'content': b'changed bytes'}], b'{"version":2}')
        self.assertEqual(b'original desired bytes', output.read_bytes())
        self.assertEqual(b'{"version":1}', (self.root / '.program-kit/managed.json').read_bytes())
        # Tempfile's outer cleanup must use extended paths for this deliberate
        # deep fixture too; production cleanup stays transaction-owned.
        shutil.rmtree(scratch.filesystem_path(self.root / 'deploy'))

    def setUp(self):
        parent = ROOT / 'artifacts/tests/owned-scratch'
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='s-', dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_deep_tree_is_removed_after_success_and_original_body_error(self):
        for fail in (False, True):
            body = RuntimeError('original operation failed')
            staged = None
            try:
                with scratch.owned_scratch(self.root, 'selected-roots') as staged:
                    deep = staged
                    while len(str(deep)) < 330:
                        deep /= 'package.resources.culture.' + 'x' * 28
                    Path(scratch.filesystem_path(deep)).mkdir(parents=True)
                    payload = Path(scratch.filesystem_path(deep / 'satellite.dll'))
                    payload.write_bytes(b'actual deep file')
                    self.assertGreater(len(str(deep)), 300)
                    self.assertTrue(payload.is_file())
                    if fail:
                        raise body
            except RuntimeError as error:
                self.assertTrue(fail)
                self.assertIs(body, error)
            self.assertFalse(staged.exists())

    def test_dual_failure_preserves_original_and_records_cleanup_and_residual(self):
        body = ValueError('restore failed')
        manager = scratch.owned_scratch(self.root, 'selected-roots')
        stream = io.StringIO()
        with patch.object(manager, '_remove', side_effect=OSError('handle remains open')):
            with contextlib.redirect_stderr(stream), self.assertRaises(ValueError) as observed:
                with manager:
                    raise body
        self.assertIs(body, observed.exception)
        self.assertTrue(manager.path.is_dir())
        self.assertEqual(str(manager.path), body.programkit_cleanup_failure['scratch'])
        self.assertIn('handle remains open', body.programkit_cleanup_failure['cleanupError'])
        self.assertIn('restore failed', stream.getvalue())
        manager._remove()

    def test_cleanup_failure_after_success_is_failure(self):
        manager = scratch.owned_scratch(self.root, 'release-bundle')
        with patch.object(manager, '_remove', side_effect=PermissionError('locked')):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(scratch.ScratchCleanupError) as observed:
                with manager:
                    pass
        self.assertIsNone(observed.exception.record['operationError'])
        self.assertFalse(observed.exception.record['cleanupCompleted'])
        self.assertTrue(manager.path.exists())
        manager._remove()

    def test_parent_sibling_and_outside_targets_never_get_deleted(self):
        for kind in ('parent', 'sibling', 'outside'):
            manager = scratch.owned_scratch(self.root, 'release-bundle')
            original = manager.__enter__()
            target = original.parent if kind == 'parent' else original.parent / 'sibling' if kind == 'sibling' else self.root / 'data'
            target.mkdir(exist_ok=True)
            sentinel = target / 'sentinel'
            sentinel.write_text('preserve')
            manager.path = target
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(scratch.ScratchCleanupError):
                manager.__exit__(None, None, None)
            self.assertEqual('preserve', sentinel.read_text())
            manager.path = original
            manager._remove()

    def test_replaced_root_is_not_the_owned_directory(self):
        manager = scratch.owned_scratch(self.root, 'release-bundle')
        original = manager.__enter__()
        moved = original.with_name(original.name + '-preserved')
        original.rename(moved)
        original.mkdir()
        (original / 'sentinel').write_text('replacement')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(scratch.ScratchCleanupError):
            manager.__exit__(None, None, None)
        self.assertTrue(moved.is_dir())
        self.assertEqual('replacement', (original / 'sentinel').read_text())

    def test_replaced_parent_and_artifacts_links_are_refused(self):
        manager = scratch.owned_scratch(self.root, 'release-bundle')
        original = manager.__enter__()
        parent = original.parent
        moved = parent.with_name('saved-s')
        parent.rename(moved)
        parent.mkdir()
        (parent / original.name).mkdir()
        (parent / original.name / 'sentinel').write_text('preserve')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(scratch.ScratchCleanupError):
            manager.__exit__(None, None, None)
        self.assertEqual('preserve', (parent / original.name / 'sentinel').read_text())

    def test_reparse_root_is_refused_without_following_its_target(self):
        manager = scratch.owned_scratch(self.root, 'release-bundle')
        original = manager.__enter__()
        moved = original.with_name(original.name + '-owned')
        original.rename(moved)
        target = self.root / 'unrelated'
        target.mkdir()
        sentinel = target / 'sentinel'
        sentinel.write_text('preserve')
        if os.name == 'nt':
            result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(original), str(target)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            original.symlink_to(target, target_is_directory=True)
        try:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(scratch.ScratchCleanupError):
                manager.__exit__(None, None, None)
            self.assertEqual('preserve', sentinel.read_text())
            self.assertTrue(moved.exists())
        finally:
            original.rmdir() if os.name == 'nt' else original.unlink()

    def test_platform_conversion_is_exact_and_device_or_relative_paths_fail(self):
        cases = {r'C:\work\a': '\\\\?\\C:\\work\\a',
                 '\\\\?\\C:\\work\\a': '\\\\?\\C:\\work\\a',
                 '\\\\server\\share\\a': '\\\\?\\UNC\\server\\share\\a',
                 '\\\\?\\UNC\\server\\share\\a': '\\\\?\\UNC\\server\\share\\a'}
        for value, expected in cases.items():
            self.assertEqual(expected, scratch.windows_extended_path(value))
        for value in ('relative', 'C:relative', '\\\\.\\device', '\\\\?\\GLOBALROOT\\Device'):
            with self.assertRaises(ValueError):
                scratch.windows_extended_path(value)

    def test_relative_root_unknown_purpose_and_network_root_are_not_supported(self):
        with self.assertRaisesRegex(ValueError, 'absolute'):
            scratch.owned_scratch(Path('.'), 'selected-roots')
        with self.assertRaisesRegex(ValueError, 'unknown'):
            scratch.owned_scratch(self.root, 'data')
        if os.name == 'nt':
            with patch.object(Path, 'resolve', return_value=Path('\\\\server\\share\\repo')):
                with self.assertRaisesRegex(ValueError, 'network/UNC'):
                    scratch.owned_scratch(self.root, 'selected-roots')

    def test_already_extended_local_drive_root_keeps_the_same_owned_lifecycle(self):
        if os.name == 'nt':
            with scratch.owned_scratch(Path(scratch.filesystem_path(self.root)), 'selected-roots') as staged:
                (staged / 'sentinel').write_text('owned')
                self.assertTrue(staged.is_dir())
            self.assertFalse(staged.exists())
        else:
            self.assertEqual(str(self.root), scratch.filesystem_path(self.root))


if __name__ == '__main__':
    unittest.main()
