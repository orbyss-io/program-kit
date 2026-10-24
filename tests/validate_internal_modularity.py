"""Neutral runtime isolation, standalone emission and native/tooling carrier contracts."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'extensions/program-kit-governance/scripts')]
from sync_shared_runtime import FILES, SOURCE, TARGET, sync
from release_assets import tooling_archive


class RuntimeTests(unittest.TestCase):
    def test_governance_helpers_and_emitted_eng_work_without_other_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            governance = root / 'governance'
            governance.mkdir()
            shutil.copytree(ROOT / SOURCE, governance / 'program_kit_runtime', ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('package_execution.py', 'python_runtime.py', 'tooling_witness.py'):
                shutil.copyfile(ROOT / SOURCE.parent / name, governance / name)
            (root / 'VERSION').write_text('fictional')
            (root / 'bundle.yml').write_text('fictional manifest')
            consumer = root / 'consumer'
            consumer.mkdir()
            for name in FILES:
                shutil.copyfile(ROOT / TARGET / name, consumer / name)
            script = ('import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                      'import package_execution,python_runtime,tooling_witness; '
                      'assert set(tooling_witness.inventory(Path.cwd())) == {"VERSION","bundle.yml"}; '
                      'assert package_execution.javascript_runtime().device; '
                      'assert python_runtime.contract().select(Path.cwd()); '
                      'from program_kit_runtime.test_results import test_results; '
                      'print("neutral runtime passed")')
            result = subprocess.run([sys.executable, '-I', '-c', script, str(governance)], cwd=root,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            script = ('import sys;sys.path.insert(0,sys.argv[1]); '
                      'import js_toolchain,python_runtime_contract,owned_scratch,test_results; '
                      'assert js_toolchain.device; print("standalone consumer passed")')
            result = subprocess.run([sys.executable, '-I', '-c', script, str(consumer)], cwd=root,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_shared_source_drift_refuses_without_overwriting_and_generator_repairs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / SOURCE, root / SOURCE, ignore=shutil.ignore_patterns('__pycache__'))
            sync(root, check=False)
            self.assertEqual([], sync(root))
            for name in FILES:
                for base in (SOURCE, TARGET):
                    path = root / base / name
                    path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            self.assertEqual([], sync(root), 'Native Windows CRLF checkout must retain generation parity')
            target = root / TARGET / 'test_results.py'
            target.write_bytes(b'authored edit')
            with self.assertRaisesRegex(ValueError, 'test_results.py'):
                sync(root)
            self.assertEqual(b'authored edit', target.read_bytes())
            self.assertEqual(['test_results.py'], sync(root, check=False))
            self.assertEqual([], sync(root))

    def test_named_result_failures_remain_failures(self):
        from program_kit_runtime.test_results import test_results
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'cases.xml'
            report.write_text('<testsuite><testcase classname="real" name="passed"/><testcase name="skip"><skipped/></testcase></testsuite>')
            self.assertEqual({'real.passed': True, 'skip': False}, test_results(report, 'junit'))
            for text in ('<testsuite/>', '<testsuite><testcase name="same"/><testcase name="same"/></testsuite>'):
                report.write_text(text)
                with self.assertRaises(ValueError): test_results(report, 'junit')

    def test_tooling_selection_keeps_predecessors_but_rejects_thin_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'program-kit-1.0.zip'
            with zipfile.ZipFile(old, 'w') as archive:
                archive.writestr('scripts/upgrade_program_kit.py', 'legacy source')
            self.assertEqual(old, tooling_archive(root, '1.0'))
            with zipfile.ZipFile(old, 'w') as archive:
                archive.writestr('bundle.yml', 'composition only')
            with self.assertRaisesRegex(FileNotFoundError, 'composition bundle'):
                tooling_archive(root, '1.0')
            current = root / 'program-kit-tooling-1.0.zip'
            current.write_bytes(b'fixture selection only')
            self.assertEqual(current, tooling_archive(root, '1.0'))


class DistributionTests(unittest.TestCase):
    def test_native_limit_is_separate_and_bad_members_refuse(self):
        from build_release import validate_distribution_archive
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as contents:
                for index in range(513): contents.writestr(f'sources/{index}.txt', b'original')
            with self.assertRaisesRegex(ValueError, '512-entry'):
                validate_distribution_archive(archive)
            self.assertEqual(513, validate_distribution_archive(archive, tooling=True)['entries'])
            for names in (('../escape',), ('a', 'A'), ('C:/outside',), ('source\\escape',)):
                with zipfile.ZipFile(archive, 'w') as contents:
                    for name in names:
                        member = zipfile.ZipInfo('placeholder')
                        member.filename = name
                        contents.writestr(member, b'original')
                with self.subTest(names=names), self.assertRaisesRegex(ValueError, 'Unsafe or duplicate'):
                    validate_distribution_archive(archive, tooling=True)
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as contents:
                contents.writestr('oversized', b'x' * (10 * 1_048_576 + 1))
            with self.assertRaisesRegex(ValueError, 'member/total byte bound'):
                validate_distribution_archive(archive, tooling=True)


if __name__ == '__main__':
    unittest.main()
