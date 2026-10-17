"""Installed native web wrappers: runtime propagation, no implicit acquisition."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path.insert(0, str(TEMPLATE / 'files/eng'))
import python_runtime_contract as runtime


class WebRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pk web runtime ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.eng = self.root / 'eng'
        (self.eng / 'web').mkdir(parents=True)
        for filename in ('Test-Web.ps1', 'Prepare-Web.ps1'):
            shutil.copyfile(TEMPLATE / 'web-profiles/common/eng' / filename, self.eng / filename)
        shutil.copyfile(TEMPLATE / 'files/eng/ProgramKitPython.psm1', self.eng / 'ProgramKitPython.psm1')
        shutil.copyfile(TEMPLATE / 'files/eng/python_runtime_contract.py', self.eng / 'python_runtime_contract.py')
        (self.root / '.specify').mkdir()
        (self.root / '.specify/python-runtime.json').write_text(json.dumps({'contractVersion': 1, 'executable': sys.executable}))
        (self.root / '.python-version').write_text('.'.join(map(str, sys.version_info[:3])))
        (self.eng / 'web-profile.json').write_text(json.dumps({'profile': 'bff-cookie-v1'}))
        self.log = self.root / 'calls.jsonl'
        self.env = dict(os.environ, SPECKIT_PYTHON=sys.executable, PK_WEB_CALLS=str(self.log), PYTHONUTF8='1')
        self.shell = (shutil.which('powershell') if os.name == 'nt' else None) or shutil.which('pwsh')
        self.assertTrue(self.shell, 'PowerShell is required')
        recorder = '''import json,os,subprocess,sys
from pathlib import Path
child=subprocess.run([sys.executable,'-c','import json,os,sys; print(json.dumps([sys.executable,os.environ.get("SPECKIT_PYTHON")]))'],check=True,capture_output=True,text=True)
with Path(os.environ['PK_WEB_CALLS']).open('a',encoding='utf-8') as out:
 out.write(json.dumps({'script':Path(__file__).name,'args':sys.argv[1:],'python':sys.executable,'selected':os.environ.get('SPECKIT_PYTHON'),'grandchild':json.loads(child.stdout),'browserCache':os.environ.get('PLAYWRIGHT_BROWSERS_PATH'),'cwd':os.getcwd()})+'\\n')
if Path(__file__).name=='web_identity.py': print('{}')
if Path(__file__).name=='web_readiness.py' and os.environ.get('PK_UNPREPARED'): sys.exit(19)
'''
        for filename in ('web_identity.py', 'toolchain.py', 'js_toolchain.py', 'web_readiness.py'):
            (self.eng / filename).write_text(recorder, encoding='utf-8')

    def invoke(self, filename):
        # The driver observes the same PowerShell process after the command,
        # including failure. No ambient process environment may leak out.
        driver = self.root / 'driver.ps1'
        driver.write_text('''param([string]$CommandPath)
$env:PLAYWRIGHT_BROWSERS_PATH = 'prior-cache'
$env:PROGRAMKIT_BASE_URL = 'prior-url'
$before = $env:SPECKIT_PYTHON
$failed = $false
try { & $CommandPath } catch { $failed=$true; [Console]::Error.WriteLine($_.Exception.Message) }
if ($env:PLAYWRIGHT_BROWSERS_PATH -ne 'prior-cache' -or $env:PROGRAMKIT_BASE_URL -ne 'prior-url' -or $env:SPECKIT_PYTHON -ne $before) { throw 'Environment leaked' }
if ($failed) { exit 1 }
''', encoding='utf-8')
        return subprocess.run([self.shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(driver), str(self.eng / filename)],
                              cwd=self.root, env=self.env, capture_output=True, text=True, timeout=60)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()] if self.log.exists() else []

    def test_verification_propagates_absolute_runtime_to_children_and_grandchildren_without_acquisition(self):
        result = self.invoke('Test-Web.ps1')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = self.calls()
        self.assertEqual(['web_identity.py', 'toolchain.py', 'web_readiness.py', 'js_toolchain.py', 'js_toolchain.py', 'js_toolchain.py'], [row['script'] for row in calls])
        for row in calls:
            self.assertTrue(Path(row['python']).samefile(sys.executable))
            self.assertTrue(Path(row['selected']).samefile(sys.executable))
            self.assertTrue(all(Path(value).samefile(sys.executable) for value in row['grandchild']))
            self.assertEqual(str(self.root / 'artifacts/cache/playwright-browsers'), row['browserCache'])
            self.assertFalse({'ci', 'install', 'exec', 'npx', '--with-deps'} & set(row['args']))

    def test_unprepared_check_fails_before_typecheck_or_browser_and_restores_environment(self):
        self.env['PK_UNPREPARED'] = '1'
        result = self.invoke('Test-Web.ps1')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Prepare-Web.ps1', result.stderr)
        self.assertEqual(['web_identity.py', 'toolchain.py', 'web_readiness.py'], [row['script'] for row in self.calls()])

    def test_explicit_preparation_owns_acquisition_without_device_dependency_install(self):
        result = self.invoke('Prepare-Web.ps1')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = self.calls()
        self.assertEqual(['toolchain.py', 'js_toolchain.py', 'js_toolchain.py', 'web_readiness.py'], [row['script'] for row in calls])
        self.assertIn('ci', calls[1]['args'])
        self.assertEqual(['exec', '--no', '--', 'playwright', 'install', 'chromium'], calls[2]['args'][-6:])
        self.assertNotIn('--with-deps', str(calls))

    def test_runtime_mismatch_or_stale_pin_stops_before_adapter_dispatch(self):
        for record in ({'contractVersion': 1, 'executable': str(self.root / 'missing-python')}, {'contractVersion': 7, 'executable': sys.executable}):
            (self.root / '.specify/python-runtime.json').write_text(json.dumps(record))
            result = self.invoke('Test-Web.ps1')
            self.assertNotEqual(0, result.returncode)
            self.assertIn('PKV005', result.stderr)
            self.assertEqual([], self.calls())
        (self.root / '.specify/python-runtime.json').write_text(json.dumps({'contractVersion': 1, 'executable': sys.executable}))
        (self.root / '.python-version').write_text('0.0.0')
        result = self.invoke('Test-Web.ps1')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('.python-version', result.stderr)
        self.assertEqual([], self.calls())

    def test_applicable_dependency_probe_fails_only_for_selected_workflow(self):
        # A real isolated interpreter without site packages is still sufficient
        # for stdlib engineering. The missing workflow module is not fabricated
        # by a validator returning a canned failure.
        isolated = self.root / 'isolated'
        subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(isolated)], check=True,
                       capture_output=True, text=True, timeout=60)
        executable = isolated / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        (self.root / '.specify/python-runtime.json').write_text(json.dumps({'contractVersion': 1, 'executable': str(executable)}))
        with patch.dict(os.environ, SPECKIT_PYTHON=str(executable)):
            admitted = runtime.verify(self.root, purpose='engineering')
            self.assertEqual({}, admitted['modules'])
            with self.assertRaisesRegex(ValueError, 'workflow readiness failed.*required dependencies') as failure:
                runtime.verify(self.root, purpose='workflow')
            self.assertIn("No module named 'yaml'", str(failure.exception))
        self.assertFalse((isolated / 'Scripts/pip.exe').exists())

    def test_real_node_missing_dependency_admission_is_read_only(self):
        import web_readiness
        node = shutil.which('node')
        self.assertTrue(node, 'Node is required for the web dependency admission probe')
        evidence = self.root / 'evidence.json'
        original = json.dumps({'commands': {'node': [node]}}).encode()
        evidence.write_bytes(original)
        (self.eng / 'web/package.json').write_text(json.dumps({'devDependencies': {'@playwright/test': '1.64.1'}}))
        with patch.object(web_readiness.js_toolchain, 'context', return_value=([], dict(os.environ))):
            with self.assertRaisesRegex(ValueError, 'PKW106.*Prepare-Web.ps1'):
                web_readiness.check(self.root, evidence)
        self.assertEqual(original, evidence.read_bytes())
        self.assertFalse((self.eng / 'web/node_modules').exists())


if __name__ == '__main__':
    unittest.main()
