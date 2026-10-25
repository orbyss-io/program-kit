"""Offline standalone worker-policy contracts; no Codex sandbox or model is launched.

A recording runner executes only the helper's generated isolated Python probe.
This checks argv, artifact verification and cleanup; actual device sandbox policy
remains a separately human-owned observation.
"""
from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess
import sys
import unittest
from unittest.mock import patch

from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import codex_worker_policy as policy


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


class WorkerPolicyTests(unittest.TestCase):
    def test_unsafe_extra_arguments_refuse_without_execution_or_environment_mutation(self):
        before = dict(os.environ)
        for arguments in ('--sandbox read-only', '--sandbox danger-full-access', '-sdanger-full-access',
                '--dangerously-bypass-approvals-and-sandbox', '--add-dir C:/', '--worktree',
                '-c sandbox_mode="danger-full-access"', '-c permissions.default=all',
                '-c sandbox_workspace_write.writable_roots=[]', '--approve-for-me',
                '--permission-profile full', '--cd C:/', '--full-auto', '--model', '"broken'):
            with self.subTest(arguments=arguments), patch.object(subprocess, 'run', side_effect=AssertionError('Unsafe argv started a process')):
                with self.assertRaises(policy.WorkerPolicyError):
                    policy.parse_extra(arguments)
        for arguments in ('', '--sandbox workspace-write --sandbox workspace-write'):
            with self.assertRaises(policy.WorkerPolicyError):
                policy.parse_extra(arguments, require_write=True)
        self.assertEqual(before, dict(os.environ))

    def test_allowed_model_profile_output_and_reasoning_arguments_round_trip(self):
        self.assertEqual(['-m', 'model name', '--profile', 'profile name', '--json'],
            policy.parse_extra('--sandbox=workspace-write -m "model name" --profile "profile name" --json', require_write=True))
        self.assertEqual(['-c', 'model_reasoning_effort="high"'],
            policy.parse_extra('-s workspace-write -c \'model_reasoning_effort="high"\''))

    def test_actual_specify_adapter_requires_explicit_sandbox_without_dispatch(self):
        from specify_cli.integrations import get_integration
        with patch.dict(os.environ, {}, clear=True), patch.object(subprocess, 'run', side_effect=AssertionError('Adapter inspection dispatched')):
            before = get_integration('codex').build_exec_args('fixture', output_json=False)
            self.assertNotIn('--sandbox', before)
            os.environ[policy.EXTRA_ARGS] = '--sandbox workspace-write --profile "fixture profile"'
            with patch.object(policy.shutil, 'which', return_value='fixture-codex') as executable:
                after = policy.inspect_adapter()
            executable.assert_called_once()
            self.assertEqual(['fixture-codex', 'exec', 'Program Kit permission check'], after[:3])
            self.assertEqual(['--profile', 'fixture profile'], policy.parse_extra(shlex.join(after[3:]), require_write=True))
            for arguments in ([], ['codex', 'bad', 'fixture'], ['codex', 'exec', 'fixture'],
                              ['codex', 'exec', 'fixture', '--sandbox', 'danger-full-access']):
                with self.subTest(arguments=arguments), patch.object(type(get_integration('codex')), 'build_exec_args', return_value=arguments):
                    with self.assertRaises(policy.WorkerPolicyError):
                        policy.inspect_adapter()
            with patch.object(policy.shutil, 'which', return_value=None):
                with self.assertRaisesRegex(policy.WorkerPolicyError, 'unavailable'):
                    policy.inspect_adapter()

    def fixture(self, root, *, unreadable=False, runner=None):
        argv = ['fixture-codex', 'exec', 'Program Kit permission check', '--sandbox', 'workspace-write',
                '--profile', 'fixture profile', '-c', 'model_reasoning_effort="high"', '--model', 'fixture model', '--json']
        calls = []
        def recording(command, **kwargs):
            calls.append(command)
            self.assertEqual(['fixture-codex', 'sandbox'], command[:2])
            self.assertEqual(':workspace', command[command.index('--permission-profile') + 1])
            self.assertIn('--include-managed-config', command)
            self.assertEqual(['--profile', 'fixture profile', '-c', 'model_reasoning_effort="high"'],
                             command[command.index('--include-managed-config') + 1:command.index('--cd')])
            self.assertNotIn('--model', command)
            self.assertEqual(root, kwargs['cwd'])
            self.assertEqual(60, kwargs['timeout'])
            child = command[command.index('--') + 1:]
            self.assertEqual([sys.executable, '-I'], child[:2])
            # This directly runs only the finite generated Python script. It does
            # not invoke Codex, a model, an application or a device sandbox.
            return subprocess.run(child, **kwargs)
        original_read = Path.read_text
        def denied(path, *args, **kwargs):
            if path.name.startswith('.program-kit-write-probe-'):
                raise PermissionError('synthetic cross-account artifact denial')
            return original_read(path, *args, **kwargs)
        with patch.object(policy.shutil, 'which', return_value=sys.executable), \
             patch.object(Path, 'read_text', denied if unreadable else original_read):
            result = policy.verify_windows_write(root, argv, runner=runner or recording)
        return result, calls

    def test_generated_probe_replacement_child_readback_and_cleanup(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'authored.txt').write_text('Retain authored input', encoding='utf-8')
            before = snapshot(root)
            result, calls = self.fixture(root)
            self.assertEqual(1, len(calls))
            for key in ('writesVerified', 'sandboxReadbackVerified', 'cleanupVerified'):
                self.assertTrue(result[key])
            self.assertIs(False, result['codingAgentStarted'])
            self.assertEqual(before, snapshot(root))
            self.assertEqual(['authored.txt'], sorted(path.name for path in root.iterdir()))

    def test_zero_exit_with_success_marker_but_without_writes_is_rejected(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            def no_writes(command, **kwargs):
                child = command[command.index('--') + 1:]
                return subprocess.CompletedProcess(command, 0, 'PROGRAM_KIT_WRITE_PROBE_OK:' + child[4] + '\n', '')
            with self.assertRaisesRegex(policy.WorkerPolicyError, 'human workflow account'):
                self.fixture(root, runner=no_writes)
            self.assertEqual([], list(root.iterdir()))

    def test_unreadable_replaced_artifact_is_rejected_and_cleaned(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / 'authored.txt').write_text('Preserved', encoding='utf-8')
            before = snapshot(root)
            with self.assertRaisesRegex(policy.WorkerPolicyError, 'human workflow account'):
                self.fixture(root, unreadable=True)
            self.assertEqual(before, snapshot(root))
            self.assertEqual(['authored.txt'], sorted(path.name for path in root.iterdir()))

    def test_native_runner_failure_is_not_a_successful_write_probe(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            for runner in (lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 7, '', 'synthetic denial'),
                           lambda *args, **kwargs: (_ for _ in ()).throw(OSError('synthetic launch refusal'))):
                with self.assertRaises(policy.WorkerPolicyError):
                    self.fixture(root, runner=runner)
                self.assertEqual([], list(root.iterdir()))

    def test_obsolete_outer_dispatch_refuses_before_reads_writes_or_processes(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            historical = root / 'state.json'; historical.write_bytes(b'\xff preserved history')
            before = snapshot(root)
            environment = dict(os.environ)
            with patch.object(Path, 'read_text', side_effect=AssertionError('Retired route read saved state')), \
                 patch.object(subprocess, 'run', side_effect=AssertionError('Retired route dispatched')), \
                 patch.object(policy, 'inspect_adapter', side_effect=AssertionError('Retired route prepared dispatch')):
                for integration in ('codex', 'claude', 'auto'):
                    with self.assertRaisesRegex(policy.WorkerPolicyError, 'dispatcher is retired'):
                        with policy.worker_environment(root, integration):
                            self.fail('Retired worker body executed')
            self.assertEqual(environment, dict(os.environ))
            self.assertEqual(before, snapshot(root))


if __name__ == '__main__':
    unittest.main()
