"""Build the actual six-project/two-frontend layout without starting infrastructure."""
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import importlib
sys.modules.setdefault('foundation_process', importlib.import_module('compatibility_process'))
import foundation_fixture


def main():
    directory = ROOT / 'artifacts/tests/composition-layout' / uuid.uuid4().hex[:8]; directory.mkdir(parents=True)
    result = {'schemaVersion': 1, 'status': 'running', 'scope': __doc__, 'runtimeAcceptanceEstablished': False}
    try:
        observed = foundation_fixture.captured([sys.executable, str(ROOT / 'tests/validate_composition_start.py')],
            ROOT, directory / 'scaffold', timeout=600)
        if observed['exitCode'] or not observed['logsDrained'] or not observed['cleanupComplete']:
            raise ValueError('Actual layout scaffolding failed; inspect ' + str(directory))
        scaffold = json.loads((directory / 'scaffold/stdout.log').read_text(encoding='utf-8'))
        root = (ROOT / scaffold['consumer']).resolve()
        if not root.is_relative_to(ROOT / 'artifacts/t') or scaffold['status'] != 'scaffolded':
            raise ValueError('Layout proof must use its new owned generated fixture')
        result['consumer'] = root.relative_to(ROOT).as_posix()
        # Import the actual emitted current adapters in a fresh native child; no
        # repository-private helper globals substitute for installed ownership.
        script = '''import json,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'scripts'))
import composition_run as run,prepare_hosted_pages
graph=run.read(root/'config/program-kit/foundation-composition.json')
projects=sorted(str(p.relative_to(root)).replace('\\\\','/') for p in (root/'src').rglob('*.csproj'))
frontends=sorted(run.model.resources(graph,'frontend'))
run.require(len(projects)==6 and len(frontends)==2,'Expected actual six-project/two-frontend layout')
command=run.Commands(root,Path(sys.argv[1])/'native')
command.run([sys.executable,'scripts/toolchain.py','--repository','.','--evidence','artifacts/program-kit/toolchain.json'])
command.run(['pwsh','-NoProfile','-File','scripts/Restore.ps1','-Subject','Application.slnx'],timeout=600)
command.run(['pwsh','-NoProfile','-File','scripts/Restore.ps1','-Subject','Application.slnx','-LockedMode'],timeout=600)
command.run(['dotnet','build','Application.slnx','-c','Release','--no-restore'],timeout=600)
prepare_hosted_pages.build(root,graph,command,restore=True)
for name in frontends:prepare_hosted_pages.admission(root,graph,name)
print(json.dumps({'projects':projects,'frontends':frontends,'sdkBuild':True,'lockedRestore':True,'nativeViteBuilds':True}))
'''
        observed = foundation_fixture.captured([sys.executable, '-c', script, str(directory)], root, directory / 'execution', timeout=1800)
        if observed['exitCode'] or not observed['logsDrained'] or not observed['cleanupComplete']:
            raise ValueError('Actual SDK/frontend layout build failed; inspect ' + str(directory))
        output = (directory / 'execution/stdout.log').read_text(encoding='utf-8')
        result.update(json.loads(output.strip().splitlines()[-1]), status='passed')
    except BaseException as error:
        result.update(status='failed', diagnostic=str(error)); raise
    finally:
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('Actual generated layout proof: ' + str(directory / 'results.json'))


if __name__ == '__main__': main()
