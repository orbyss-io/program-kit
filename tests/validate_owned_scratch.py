"""Owned scratch lifecycle, deep Windows paths, and separate failure observations."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import owned_scratch as scratch


class OwnedScratchTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Native Windows governance sharing')
    def test_governance_replacement_recovers_short_block_and_preserves_persistent_failure(self):
        import governance_state as governance
        import threading
        import time
        target = self.root / 'traceability.md'
        governance.write_text(target, 'original document\n')
        with self.locked_file(target) as release:
            thread = threading.Thread(target=lambda: (time.sleep(.06), release()))
            thread.start()
            try:
                governance.write_text(target, 'new document\n')
            finally:
                thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        self.assertEqual('new document\n', target.read_text())
        with self.locked_file(target):
            with self.assertRaises(PermissionError): governance.write_text(target, 'blocked document')
        self.assertEqual('new document\n', target.read_text())
        self.assertFalse(list(self.root.glob('.traceability.md.*.tmp')))

    @unittest.skipUnless(os.name == 'nt', 'Windows governance concurrent-edit boundary')
    def test_governance_replacement_refuses_concurrent_edit_and_unreadable_snapshot(self):
        import governance_state as governance
        import windows_workflow_path as paths
        target = self.root / 'traceability.md'
        target.write_text('original document')
        failure = PermissionError('concurrent document edit'); failure.winerror = 32
        def blocked(*_):
            target.write_text('concurrent document')
            raise failure
        with patch.object(paths.os, 'replace', side_effect=blocked) as replace:
            with self.assertRaises(PermissionError): governance.write_text(target, 'stale document')
            replace.assert_called_once()
        self.assertEqual('concurrent document', target.read_text())
        self.assertFalse(list(self.root.glob('.traceability.md.*.tmp')))
        with patch.object(paths, 'file_snapshot', side_effect=PermissionError('cannot inspect original')):
            with self.assertRaises(PermissionError): governance.write_text(target, 'must not write')
        self.assertEqual('concurrent document', target.read_text())

    @contextlib.contextmanager
    def locked_file(self, path):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                      wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 128, None)
        self.assertNotEqual(ctypes.c_void_p(-1).value, handle, ctypes.get_last_error())
        closed = False
        def release():
            nonlocal closed
            if not closed:
                kernel.CloseHandle(handle)
                closed = True
        try:
            yield release
        finally:
            release()

    @unittest.skipUnless(os.name == 'nt', 'Native Windows transaction sharing')
    def test_transaction_replacement_recovers_short_block_and_refuses_persistent_block(self):
        import reconciliation
        import threading
        import time
        target = self.root / 'journal.json'
        target.write_bytes(b'original journal')
        with self.locked_file(target) as release:
            thread = threading.Thread(target=lambda: (time.sleep(.06), release()))
            thread.start()
            try:
                reconciliation.atomic_write(target, b'new journal', 'journal')
            finally:
                thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        self.assertEqual(b'new journal', target.read_bytes())
        with self.locked_file(target):
            with self.assertRaises(PermissionError):
                reconciliation.atomic_write(target, b'must not replace', 'journal')
        self.assertEqual(b'new journal', target.read_bytes())
        self.assertFalse(target.with_name('journal.json.journal.tmp').exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows transaction retry boundary')
    def test_transaction_retry_refuses_changed_destination(self):
        import reconciliation
        target = self.root / 'journal.json'
        target.write_bytes(b'original journal')
        failure = PermissionError('observed concurrent edit')
        failure.winerror = 32
        def blocked(*_):
            target.write_bytes(b'concurrent journal')
            raise failure
        with patch.object(reconciliation.os, 'replace', side_effect=blocked) as replace:
            with self.assertRaises(PermissionError):
                reconciliation.atomic_write(target, b'stale journal', 'journal')
            replace.assert_called_once()
        self.assertEqual(b'concurrent journal', target.read_bytes())
        self.assertFalse(target.with_name('journal.json.journal.tmp').exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows read-only Git objects')
    def test_real_disposable_git_objects_are_removed_without_touching_sibling_data(self):
        sentinel = self.root / 'retained-data'
        sentinel.write_text('preserve')
        # Exercise both actual rmtree callback APIs on the current interpreter;
        # this does not claim that a Python 3.11 interpreter was executed.
        for version in (sys.version_info, (3, 11, 0)):
            with self.subTest(callbackApi=version[:2]), patch.object(scratch.sys, 'version_info', version):
                manager = scratch.owned_scratch(self.root, 'validation-fixture')
                with manager as directory:
                    for command in (['init', '-q'], ['hash-object', '-w', '--stdin']):
                        result = subprocess.run(['git', '-C', str(directory), *command], input=b'owned fixture object\n',
                                                capture_output=True, check=True)
                    object_id = result.stdout.decode('ascii').strip()
                    stored = directory / '.git/objects' / object_id[:2] / object_id[2:]
                    self.assertTrue(stored.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
                self.assertFalse(directory.exists())
        self.assertEqual('preserve', sentinel.read_text())

    @unittest.skipUnless(os.name == 'nt', 'Windows read-only bit contract')
    def test_readonly_recovery_refuses_outside_paths_and_plain_access_denial(self):
        manager = scratch.owned_scratch(self.root, 'validation-fixture')
        with manager as directory:
            outside = self.root / 'retained-readonly'
            outside.write_text('preserve')
            os.chmod(outside, stat.S_IREAD)
            try:
                failure = PermissionError('outside deletion refused')
                with self.assertRaises(PermissionError) as observed:
                    manager._remove_readonly_file(os.unlink, str(outside), failure)
                self.assertIs(failure, observed.exception)
                self.assertTrue(outside.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
                self.assertEqual('preserve', outside.read_text())
            finally:
                os.chmod(outside, stat.S_IWRITE)
            writable = directory / 'writable'
            writable.write_text('preserve access error')
            failure = PermissionError('not a read-only failure')
            with self.assertRaises(PermissionError) as observed:
                manager._remove_readonly_file(os.unlink, str(writable), failure)
            self.assertIs(failure, observed.exception)
            self.assertTrue(writable.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows directory junction boundary')
    def test_readonly_recovery_cannot_follow_a_nested_junction(self):
        outside = self.root / 'retained-tree'
        outside.mkdir()
        sentinel = outside / 'object'
        sentinel.write_text('preserve')
        os.chmod(sentinel, stat.S_IREAD)
        try:
            manager = scratch.owned_scratch(self.root, 'validation-fixture')
            with manager as directory:
                junction = directory / 'borrowed'
                result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(junction), str(outside)],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                with self.assertRaisesRegex(ValueError, 'links or reparse points'):
                    manager._remove_readonly_file(os.unlink, str(junction / 'object'), PermissionError('read-only'))
                self.assertTrue(sentinel.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
                self.assertEqual('preserve', sentinel.read_text())
            self.assertTrue(sentinel.exists())
        finally:
            os.chmod(sentinel, stat.S_IWRITE)

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
