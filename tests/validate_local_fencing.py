"""Real local cross-process fencing/crash tests using only owned synthetic resources."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'extensions/program-kit-dotnet/references/examples/local-fencing/local_fencing.py'
spec = importlib.util.spec_from_file_location('local_fencing_reference', SOURCE)
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
RUN = ROOT/'artifacts/local-fencing'/uuid.uuid4().hex
RUN.mkdir(parents=True)


def storage_identity():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        native = ctypes.WinDLL('kernel32', use_last_error=True)
        native.GetVolumePathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        native.GetVolumePathNameW.restype = wintypes.BOOL
        native.GetVolumeInformationW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD]
        native.GetVolumeInformationW.restype = wintypes.BOOL
        native.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]; native.GetDriveTypeW.restype = wintypes.UINT
        volume, filesystem = ctypes.create_unicode_buffer(1024), ctypes.create_unicode_buffer(64)
        serial, maximum, flags = wintypes.DWORD(), wintypes.DWORD(), wintypes.DWORD()
        assert native.GetVolumePathNameW(str(ROOT), volume, len(volume)), 'Cannot observe owned fixture volume'
        assert native.GetVolumeInformationW(volume.value, None, 0, ctypes.byref(serial), ctypes.byref(maximum), ctypes.byref(flags), filesystem, len(filesystem))
        assert native.GetDriveTypeW(volume.value) == 3, 'Reference qualifies local fixed storage only'
        return {'filesystem': filesystem.value, 'driveType': 'local-fixed', 'volumeSerial': serial.value}
    return {'filesystem': subprocess.check_output(['stat', '-f', '-c', '%T', str(ROOT)], text=True).strip(),
            'device': os.stat(ROOT).st_dev, 'scope': 'This actual local CI mount only; no network/shared-volume guarantee'}


class FencingTests(unittest.TestCase):
    def setUp(self):
        self.parent = ROOT/'artifacts/t'/('fence-'+uuid.uuid4().hex[:12]); self.parent.mkdir(parents=True)
        self.resource = f.Resource.provision(self.parent/'resource')
        self.log = RUN/self._testMethodName; self.log.mkdir()
        self.children = 0
        (self.log/'fixture.json').write_text(json.dumps({'root': str(self.resource.root), 'synthetic': True}))

    def issue(self, action='publish', content=b'original', work='work', operation='operation', deadline=None):
        return self.resource.store.issue(work, operation, action, f.digest(content) if action == 'publish' else None, deadline=deadline)

    def publish(self, content=b'original', **kwargs):
        ticket = self.issue(content=content, **kwargs); self.resource.admit(ticket)
        self.resource.effect(ticket, self.resource.stage(ticket, content)); return ticket

    def worker(self, request, expected=0):
        path = self.parent/('request-'+uuid.uuid4().hex+'.json'); path.write_text(json.dumps(request))
        index = self.children; self.children += 1
        command = [sys.executable, '-E', '-s', str(SOURCE), '--root', str(self.resource.root), '--request', str(path)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill(); stdout, stderr = process.communicate(timeout=5)
            raise
        native = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        (self.log/f'{index}.stdout.log').write_text(native.stdout, encoding='utf-8')
        (self.log/f'{index}.stderr.log').write_text(native.stderr, encoding='utf-8')
        (self.log/f'{index}.exit.json').write_text(json.dumps({'processId': process.pid, 'exitCode': native.returncode,
                                                             'expectedExitCode': expected, 'command': command}))
        self.assertEqual(expected, native.returncode, native.stdout+native.stderr)
        return json.loads(native.stdout)['result'] if expected == 0 else native

    @contextmanager
    def paused(self, request, ready_name='ready'):
        path = self.parent/('request-'+uuid.uuid4().hex+'.json'); path.write_text(json.dumps(request))
        process = subprocess.Popen([sys.executable, '-E', '-s', str(SOURCE), '--root', str(self.resource.root), '--request', str(path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        index = self.children; self.children += 1
        try:
            until = time.monotonic()+5
            while not (self.resource.root/'control'/ready_name).is_file():
                self.assertIsNone(process.poll(), 'Owned fixture process exited before the actual pause/guard acquisition')
                self.assertLess(time.monotonic(), until, 'Owned fixture pause was not observed')
                time.sleep(0.005)
            yield process
        finally:
            (self.resource.root/'control/release').write_text('release')
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()  # This exact owned process has no descendant launch path.
                stdout, stderr = process.communicate(timeout=5)
                self.fail('Owned synthetic process exceeded cleanup deadline')
            finally:
                (self.log/f'{index}.stdout.log').write_text(stdout, encoding='utf-8')
                (self.log/f'{index}.stderr.log').write_text(stderr, encoding='utf-8')
                (self.log/f'{index}.exit.json').write_text(json.dumps({'processId': process.pid, 'exitCode': process.returncode}))

    def recovery(self, expected):
        ticket = self.issue('reconcile', work='recovery', operation='recover')
        self.worker({'method': 'admit', 'ticket': ticket})
        observation = self.worker({'method': 'observe', 'ticket': ticket})
        self.assertEqual(expected, self.worker({'method': 'reconcile', 'ticket': ticket, 'observation': observation}))
        return ticket

    def test_paused_producer_cannot_resurrect_erased_object_or_clean_another_stage(self):
        old = self.issue(); self.resource.admit(old)
        other = self.issue(work='other', operation='other', content=b'other')
        other_stage = self.resource.stage(other, b'other')
        with self.paused({'method': 'publish', 'ticket': old, 'contentHex': b'original'.hex(), 'pause': True,
                          'pauseDeadline': time.time_ns()+10_000_000_000}) as process:
            original_stage = f.document(self.resource.root/'control/ready')['stage']
            erase = self.issue('erase', work='erase', operation='erase'); self.resource.admit(erase)
            self.worker({'method': 'erase', 'ticket': erase})
        self.assertNotEqual(0, process.returncode)
        self.assertIsNone(self.resource.physical())
        self.assertTrue(self.resource.state()['barrier'])
        self.assertFalse((self.resource.root/original_stage).exists())
        self.assertTrue((self.resource.root/other_stage).exists())
        with self.assertRaises(f.Denied): self.resource.admit(self.issue(work='new', operation='new'))

    def test_stale_producer_and_paused_remover_cannot_damage_newer_publication(self):
        old = self.publish()
        erase = self.issue('erase', work='erase', operation='erase'); self.resource.admit(erase)
        with self.paused({'method': 'erase', 'ticket': erase, 'pause': True, 'pauseDeadline': time.time_ns()+10_000_000_000}) as process:
            newer = self.publish(b'new', work='new', operation='new')
            self.worker({'method': 'publish', 'ticket': old, 'contentHex': b'original'.hex()}, expected=1)
        self.assertNotEqual(0, process.returncode)
        self.assertEqual(f.digest(b'new'), self.resource.physical())
        self.assertEqual(newer['fence'], self.resource.state()['highWater'])

    def test_resource_admission_not_issuer_counter_revokes_old_physical_authority(self):
        old = self.issue(); self.resource.admit(old)
        newer = self.issue(content=b'new', work='new', operation='new')
        # Issuing durable intent alone cannot revoke an already admitted effect.
        self.resource.effect(old, self.resource.stage(old, b'original'))
        self.resource.admit(newer)
        with self.assertRaises(f.Denied): self.resource.effect(old)
        self.resource.effect(newer, self.resource.stage(newer, b'new'))

    def test_actual_restart_preserves_highwater_barrier_and_legacy_denial(self):
        self.publish()
        erase = self.issue('erase', work='erase', operation='erase'); self.resource.admit(erase); self.resource.effect(erase)
        observed = self.worker({'method': 'inspect'})
        self.assertTrue(observed['state']['barrier']); self.assertEqual(erase['fence'], observed['state']['highWater'])
        self.assertFalse(observed['authorityGranted'])
        restarted = f.Resource(self.resource.root)
        for method in (restarted.legacy_publish, restarted.legacy_erase):
            with self.assertRaises(f.Denied): method(b'original')
        with self.assertRaises(FileExistsError): f.Resource.provision(self.resource.root)

    def test_same_fence_replay_is_exact_and_expired_replay_has_no_authority(self):
        ticket = self.publish(); stamp = self.resource.payload.stat().st_mtime_ns
        self.assertEqual('replayed', self.resource.effect(ticket))
        self.assertEqual(stamp, self.resource.payload.stat().st_mtime_ns)
        for field, value in [('work', 'other'), ('operation', 'other'), ('payload', '0'*64), ('resource', 'other')]:
            with self.assertRaises(f.Denied): self.resource.effect({**ticket, field: value})
        self.resource.clock = lambda: ticket['deadline']
        with self.assertRaises(f.Denied): self.resource.effect(ticket)
        self.assertEqual(stamp, self.resource.payload.stat().st_mtime_ns)

    def test_deadline_equality_before_admission_and_after_input_wait(self):
        ticket = self.issue(); before = self.resource.authority.read_bytes()
        self.resource.clock = lambda: ticket['deadline']
        with self.assertRaises(f.Denied): self.resource.admit(ticket)
        self.assertEqual(before, self.resource.authority.read_bytes())
        self.resource.clock = time.time_ns
        ticket = self.issue(deadline=time.time_ns()+500_000_000); self.resource.admit(ticket)
        with self.paused({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex(), 'pause': True,
                          'pauseDeadline': time.time_ns()+10_000_000_000}) as process:
            while time.time_ns() < ticket['deadline']: time.sleep(0.005)
        self.assertNotEqual(0, process.returncode); self.assertIsNone(self.resource.physical())

    def test_deadline_is_rechecked_after_real_cross_process_guard_wait(self):
        ticket = self.issue(deadline=time.time_ns()+500_000_000); self.resource.admit(ticket)
        with self.paused({'method': 'hold', 'deadline': time.time_ns()+10_000_000_000}):
            native = self.worker({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex()}, expected=1)
            self.assertIn('waiting for the physical guard', native.stderr)
            self.assertTrue((self.resource.root/'control'/('waiting-'+str(ticket['fence']))).is_file())
        self.assertIsNone(self.resource.physical()); self.assertIsNone(self.resource.state()['effect'])

    def test_cancellation_after_input_and_guard_wait_is_bound_to_exact_fence(self):
        ticket = self.issue(); self.resource.admit(ticket)
        with self.paused({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex(), 'pause': True,
                          'pauseDeadline': time.time_ns()+10_000_000_000}) as process:
            (self.resource.root/'control'/('cancel-'+str(ticket['fence']))).write_text('observed cancellation')
        self.assertNotEqual(0, process.returncode); self.assertIsNone(self.resource.physical())
        (self.resource.root/'control/ready').unlink(); (self.resource.root/'control/release').unlink()
        later = self.issue(work='later', operation='later'); self.resource.admit(later)
        with self.paused({'method': 'hold', 'deadline': time.time_ns()+10_000_000_000}):
            with self.paused({'method': 'publish', 'ticket': later, 'contentHex': b'original'.hex()}, ready_name='waiting-'+str(later['fence'])) as waiter:
                (self.resource.root/'control'/('cancel-'+str(later['fence']))).write_text('observed cancellation')
            self.assertNotEqual(0, waiter.returncode)
        self.assertIsNone(self.resource.physical())
        final = self.issue(work='final', operation='final'); self.resource.admit(final)
        self.worker({'method': 'publish', 'ticket': final, 'contentHex': b'original'.hex()})

    def test_missing_corrupt_duplicate_authority_never_resets_to_zero(self):
        self.publish(); original = self.resource.authority.read_bytes()
        self.resource.authority.unlink()
        with self.assertRaises(f.Denied): self.resource.inspect()
        with self.assertRaises(FileExistsError): f.Resource.provision(self.resource.root)
        for content in (b'{', b'{"schemaVersion":1,"schemaVersion":1}',
                        f.canonical({**json.loads(original), 'schemaVersion': True}),
                        f.canonical({**json.loads(original), 'highWater': 0, 'owner': None, 'effect': None})):
            self.resource.authority.write_bytes(content)
            with self.assertRaises((f.Denied, json.JSONDecodeError)): self.resource.inspect()
        self.resource.authority.write_bytes(original)
        self.assertEqual(f.digest(b'original'), self.resource.physical())

    def test_missing_work_store_or_guard_never_creates_authority(self):
        ticket = self.issue()
        self.resource.store.path.unlink()
        with self.assertRaises(f.Denied): self.resource.admit(ticket)
        self.assertFalse(self.resource.store.path.exists())
        self.resource.root.joinpath('guard.lock').unlink()
        with self.assertRaises(f.Denied): self.resource.inspect()

    def test_counter_reuse_overflow_and_conflicting_work_identity_fail(self):
        ticket = self.publish()
        with self.assertRaises(f.Denied): self.issue(content=b'changed')
        with self.resource.store.connect() as connection:
            connection.execute("update sqlite_sequence set seq=? where name='work'", (f.MAX_COUNTER,))
        with self.assertRaises(sqlite3.OperationalError): self.issue(work='new', operation='new')
        self.assertEqual(ticket['fence'], self.resource.state()['highWater'])
        # A recreated/different identity cannot use its own low counter to reset a resource.
        with self.assertRaises(f.Denied): self.resource.admit({**ticket, 'resource': uuid.uuid4().hex, 'fence': 1})

    def test_publish_process_crash_windows_reconcile_independent_physical_and_work_state(self):
        parent = self.parent
        for fault in ('after-intent', 'after-effect', 'after-completion'):
            self.resource = f.Resource.provision(parent/fault)
            ticket = self.issue(); self.resource.admit(ticket)
            self.worker({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex(), 'fault': fault}, expected=91)
            actual = self.worker({'method': 'inspect'})
            applied = fault != 'after-intent'
            self.assertEqual(f.digest(b'original') if applied else None, actual['payload'])
            self.assertEqual('committed', self.resource.store.status(ticket['fence']))
            stamp = self.resource.payload.stat().st_mtime_ns if applied else None
            if fault != 'after-completion':
                self.worker({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex()}, expected=1)
            self.recovery('observed-completed' if applied else 'observed-not-applied')
            if applied:
                self.assertEqual(stamp, self.resource.payload.stat().st_mtime_ns)
                self.assertEqual('completed', self.resource.store.status(ticket['fence']))
            else:
                later = self.issue(); self.resource.admit(later)
                self.resource.effect(later, self.resource.stage(later, b'original'))
            self.assertEqual(f.digest(b'original'), self.resource.physical())

    def test_erase_crash_windows_retain_removal_protection_and_observed_recovery(self):
        parent = self.parent
        for fault in ('after-intent', 'after-effect', 'after-completion'):
            self.resource = f.Resource.provision(parent/fault)
            old = self.publish()
            erase = self.issue('erase', work='erase', operation='erase'); self.resource.admit(erase)
            self.worker({'method': 'erase', 'ticket': erase, 'fault': fault}, expected=91)
            actual = self.worker({'method': 'inspect'})
            self.assertTrue(actual['state']['barrier'])
            self.assertEqual('committed', self.resource.store.status(erase['fence']))
            with self.assertRaises(f.Denied): self.resource.admit(self.issue(work='new', operation='new'))
            self.recovery('observed-not-applied' if fault == 'after-intent' else 'observed-completed')
            if fault == 'after-intent':
                later = self.issue('erase', work='erase', operation='erase'); self.resource.admit(later); self.resource.effect(later)
            with self.assertRaises(f.Denied): self.resource.effect(old)
            self.assertIsNone(self.resource.physical()); self.assertTrue(self.worker({'method': 'inspect'})['state']['barrier'])

    def test_admission_crash_preserves_committed_highwater_on_actual_restart(self):
        ticket = self.issue()
        self.worker({'method': 'admit', 'ticket': ticket, 'fault': 'after-admission'}, expected=91)
        self.assertEqual(ticket['fence'], self.worker({'method': 'inspect'})['state']['highWater'])
        self.assertEqual('already-admitted', self.worker({'method': 'admit', 'ticket': ticket}))
        self.worker({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex()})

    def test_stale_or_ordinary_inspection_cannot_authorize_reconciliation(self):
        ticket = self.publish()
        one = self.issue('reconcile', work='one', operation='one'); self.resource.admit(one)
        observation = self.resource.observe(one)
        two = self.issue('reconcile', work='two', operation='two'); self.resource.admit(two)
        with self.assertRaises(f.Denied): self.resource.reconcile(one, observation)
        with self.assertRaises(f.Denied): self.resource.observe(one)
        with self.assertRaises(f.Denied): self.resource.reconcile(two, self.resource.inspect())
        observation = self.resource.observe(two); self.resource.payload.write_bytes(b'foreign')
        with self.assertRaises(f.Denied): self.resource.reconcile(two, observation)
        self.assertEqual('completed', self.resource.store.status(ticket['fence']))

    def test_uncertain_conflicting_effect_is_not_blindly_replayed_or_erased(self):
        ticket = self.issue(); self.resource.admit(ticket)
        self.worker({'method': 'publish', 'ticket': ticket, 'contentHex': b'original'.hex(), 'fault': 'after-intent'}, expected=91)
        self.resource.payload.write_bytes(b'foreign')
        newer = self.issue(work='new', operation='new')
        with self.assertRaises(f.Denied): self.resource.admit(newer)
        recovery = self.issue('reconcile', work='recover', operation='recover'); self.resource.admit(recovery)
        observation = self.resource.observe(recovery)
        with self.assertRaises(f.Unavailable): self.resource.reconcile(recovery, observation)
        self.assertEqual(b'foreign', self.resource.payload.read_bytes())
        self.assertEqual('intent', self.resource.state()['effect']['phase'])

    def test_retention_capacity_refuses_new_admission_without_retiring_barriers(self):
        for index in range(f.MAX_JOURNAL):
            self.resource.admit(self.issue(work='work-'+str(index), operation='operation-'+str(index)))
        before = self.resource.authority.read_bytes()
        with self.assertRaises(f.Denied): self.resource.admit(self.issue(work='over', operation='over'))
        self.assertEqual(before, self.resource.authority.read_bytes())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FencingTests)
    names = [case.id().rsplit('.', 1)[-1] for case in suite]
    required = json.loads(SOURCE.with_name('required-cases.json').read_text())
    assert set(names) == set(required) and len(names) == len(required) == len(set(required)), 'Required fencing case removed/substituted'
    storage = storage_identity()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and not result.skipped and result.testsRun == len(required)
    (RUN/'results.json').write_text(json.dumps({'status': 'passed' if passed else 'failed', 'platform': platform.platform(), 'observedStorage': storage,
        'requiredCases': required, 'executedCases': result.testsRun, 'skippedCases': len(result.skipped),
        'sourceSha256': {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (SOURCE, Path(__file__), SOURCE.with_name('required-cases.json'))},
        'scope': 'Actual cooperating local processes, SQLite committed authority, file fence/effect and observed process-crash recovery; no power-loss, hostile-local-writer, network/shared-volume or domain/provider acceptance',
        'paidDispatch': False}, indent=2)+'\n')
    print('Local fencing evidence: '+str(RUN/'results.json'))
    raise SystemExit(0 if passed else 1)
