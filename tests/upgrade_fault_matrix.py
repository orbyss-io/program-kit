"""Actual sequential installer faults; fresh processes retry exact preserved inputs.

Only the current disposable fixture/release supplied by validate_local_upgrade is
used. The test injects named failures after real owner operations; it never patches
native Spec Kit, fabricates a cancellation, executes archived code or touches a consumer.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid

BOUNDARIES = (
    'originals-sealed', 'Install governance extension',
    'Install building-block extension', 'Install .NET extension', 'Remove prior governance preset',
    'Install governance preset', 'Refresh native phase machinery: codex',
    'Compose installed phase contributions: codex', 'Resolve bundle composition record',
    'synchronize', 'migration-written',
)

DRIVER = '''import importlib.util,json,sys
from pathlib import Path
request=json.loads(Path(sys.argv[1]).read_bytes()); target=Path(request['target'])
source=Path(request['release'])/'scripts/upgrade_program_kit.py'
sys.path.insert(0,str(source.parent))
spec=importlib.util.spec_from_file_location('fault_current_updater',source)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
wanted=request['boundary']; fired=False
def fault(boundary):
 global fired
 if not fired and boundary==wanted:
  fired=True;sys.setprofile(None)
  Path(request['marker']).write_text(json.dumps({'boundary':boundary,'injectedAfterActualOperation':True}))
  raise RuntimeError('DELIBERATE_OWNED_UPGRADE_FAULT '+boundary)
original_step=module.run_step
def step(*args,**kwargs):
 result=original_step(*args,**kwargs);fault(args[2]);return result
module.run_step=step
original_seal=module.seal_attempt
def seal(path,value):
 result=original_seal(path,value)
 if value.get('status')=='running' and value.get('componentMutationStarted') is True: fault('originals-sealed')
 return result
module.seal_attempt=seal
original_write=module.write_attempt
def write(path,value):
 result=original_write(path,value)
 if Path(path).resolve()==(target/'.program-kit/installation/migration.json').resolve(): fault('migration-written')
 return result
module.write_attempt=write
if wanted=='synchronize':
 def observe(frame,event,value):
  if event=='return' and frame.f_code.co_name=='upgrade' and frame.f_globals.get('__name__')=='program_kit_upgrade_sync': fault('synchronize')
 sys.setprofile(observe)
sys.argv=[str(source),*request['arguments']]
raise SystemExit(module.main())
'''


def exercise(project, release, fixture, original_version, expected_version):
    parent = fixture.ROOT / 'artifacts/t' / ('upgrade-faults-' + uuid.uuid4().hex[:10])
    parent.mkdir(parents=True)
    results = {'schemaVersion': 1, 'status': 'running', 'boundaries': list(BOUNDARIES),
               'cases': [], 'productAcceptanceEstablished': False, 'publicOriginEstablished': False,
               'scope': 'Current synthetic native installed baseline; actual mutations and fresh-process retry. Historical public 0.12.7 is qualified separately.'}
    runtime = fixture.load_updater().load_release_module(
        release / 'extensions/program-kit-governance/scripts/schema_runtime.py', 'fault_fixture_runtime')
    try:
        for index, boundary in enumerate(BOUNDARIES):
            directory = parent / ('b' + str(index)); directory.mkdir()
            target = Path(fixture.filesystem_path(directory / 'consumer'))
            shutil.copytree(project, target)
            runtime.record_copy(target)
            original_history = {path.relative_to(target).as_posix(): path.read_bytes()
                for path in (target / 'docs').rglob('*') if path.is_file()}
            marker = target / 'deliberate-fault.json'
            arguments = ['--release-root', str(release), '--target', str(target), '--integration', 'codex', '--offline']
            request = directory / 'request.json'; request.write_text(json.dumps({'release': str(release),
                'target': str(target), 'boundary': boundary, 'marker': str(marker), 'arguments': arguments}), encoding='utf-8')
            driver = directory / 'fault.py'; driver.write_text(DRIVER, encoding='utf-8')
            interrupted = fixture.run(sys.executable, str(driver), str(request), cwd=target)
            (directory / 'interrupted.log').write_text(interrupted.stdout + interrupted.stderr, encoding='utf-8')
            if interrupted.returncode != 2 or not marker.is_file() or 'DELIBERATE_OWNED_UPGRADE_FAULT' not in interrupted.stderr:
                raise AssertionError('Actual owned mutation did not reach its declared fault boundary: ' + boundary + '; inspect ' + str(directory))
            attempts = sorted((target / 'artifacts/program-kit/runs').glob('*/upgrade-attempt.json'))
            failed = [(path, json.loads(path.read_bytes())) for path in attempts]
            failed = [(path, value) for path, value in failed if value.get('status') == 'incomplete']
            if len(failed) != 1 or failed[0][1]['previousInstalledVersion'] != original_version:
                raise AssertionError('Fault lost exact original-version authority: ' + boundary)
            failed_path, failed_value = failed[0]; original_attempt = failed_path.read_bytes()
            retried = fixture.run(sys.executable, str(release / 'scripts/upgrade_program_kit.py'), *arguments, cwd=target)
            (directory / 'retry.log').write_text(retried.stdout + retried.stderr, encoding='utf-8')
            fixture.require_offline_setup(retried, 'fresh-process retry after ' + boundary)
            receipt = json.loads((target / '.program-kit/installation/migration.json').read_bytes())
            if receipt['fromVersion'] != original_version or receipt['toVersion'] != expected_version:
                raise AssertionError('Retry changed original migration scope: ' + boundary)
            if failed_path.read_bytes() != original_attempt or any((target / name).read_bytes() != raw for name, raw in original_history.items()):
                raise AssertionError('Retry rewrote failed evidence or original authored history: ' + boundary)
            witness = fixture.load_updater().load_release_module(
                release / 'extensions/program-kit-governance/scripts/tooling_witness.py', 'fault_original_witness')
            retained = witness.verify_attempt_inputs(target, receipt['originalInputs'], receipt['originals'])
            if retained['attempt']['previousInstalledVersion'] != original_version or receipt['originalInputs'] != failed_value['originalInputs']:
                raise AssertionError('Retry substituted its canonical original input set: ' + boundary)
            results['cases'].append({'boundary': boundary, 'status': 'passed', 'faultExit': interrupted.returncode,
                'retryExit': retried.returncode, 'originalAttemptSha256': hashlib.sha256(original_attempt).hexdigest(),
                'originalInputs': receipt['originalInputs'], 'migration': (target / '.program-kit/installation/migration.json').relative_to(
                    Path(fixture.filesystem_path(parent))).as_posix()})
            (parent / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
        results['status'] = 'passed'
    except BaseException as error:
        results.update(status='failed', diagnostic=str(error)); raise
    finally:
        (parent / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
        print('Actual owned upgrade fault matrix: ' + str(parent / 'results.json'))
