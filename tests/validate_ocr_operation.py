"""Qualify the exact public OCR SDK with recording HTTP only; no provider or model call."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT/'extensions/program-kit-dotnet/references/examples/ocr-operation'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-lock',action='store_true',help='Prepare the new exact optional example lock; never provider authority')
    args = parser.parse_args()
    evidence = ROOT/'artifacts/ocr-operation'/uuid.uuid4().hex
    evidence.mkdir(parents=True)
    consumer = ROOT/'artifacts/t'/('ocr-'+uuid.uuid4().hex[:12])
    consumer.mkdir(parents=True)
    sdk_file = ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json'
    files = [Path(__file__),sdk_file,*EXAMPLE.iterdir()]
    basis = {file.relative_to(ROOT).as_posix():hashlib.sha256(file.read_bytes()).hexdigest() for file in files
             if file.is_file() and (not args.prepare_lock or file.name!='packages.lock.json')}
    result = {'status':'running','scope':'Actual selected public SDK, recording HTTP only; no provider acceptance',
              'providerCalls':0,'modelCalls':0,'consumer':str(consumer),'steps':[]}
    env = dict(os.environ, NUGET_PACKAGES=str(consumer/'artifacts/nuget'),NUGET_HTTP_CACHE_PATH=str(consumer/'artifacts/http'),
               DOTNET_CLI_HOME=str(ROOT/'artifacts/cache/ocr-operation/dotnet'), MSBUILDDISABLENODEREUSE='1',
               DOTNET_CLI_USE_MSBUILD_SERVER='0',PYTHONUTF8='1')
    # Never make a real key available to the recording process.
    env.pop('PROGRAMKIT_OCR_API_KEY',None)
    def run(label, command):
        observed = subprocess.run(command,cwd=consumer,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
        for stream in ('stdout','stderr'):
            (evidence/(label+'.'+stream+'.log')).write_text(getattr(observed,stream),encoding='utf-8')
        result['steps'].append({'id':label,'command':command,'exitCode':observed.returncode})
        assert observed.returncode==0, str(evidence/(label+'.stdout.log'))
        return observed.stdout
    try:
        for file in EXAMPLE.iterdir():
            if file.is_file(): shutil.copyfile(file,consumer/file.name)
        shutil.copyfile(sdk_file,consumer/'global.json')
        (consumer/'NuGet.config').write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
        assert args.prepare_lock or (consumer/'packages.lock.json').is_file(), 'Prepare the new optional example lock first'
        run('restore',['dotnet','restore','OcrOperation.csproj','--configfile','NuGet.config',
                       '--force-evaluate' if args.prepare_lock else '--locked-mode','--disable-build-servers'])
        if args.prepare_lock: shutil.copyfile(consumer/'packages.lock.json',EXAMPLE/'packages.lock.json')
        run('build',['dotnet','build','OcrOperation.csproj','--no-restore','--disable-build-servers','-m:1'])
        native = json.loads(run('native-recording',['dotnet',str(consumer/'bin/Debug/net10.0/OcrOperation.dll'),'recording-tests']))
        required = json.loads((EXAMPLE/'required-cases.json').read_text())
        assert native['status']=='passed' and native['providerCalls']==0 and native['modelCalls']==0 and native['providerAcceptance'] is False
        assert len(native['cases'])==len(set(native['cases'])) and set(native['cases'])==set(required), 'Required native case omitted/substituted'
        executed = {}
        assets = json.loads((consumer/'obj/project.assets.json').read_text())['targets']['net10.0']
        for package, details in assets.items():
            identity,version = package.split('/')
            archive = Path(env['NUGET_PACKAGES'])/identity.lower()/version/(identity.lower()+'.'+version+'.nupkg')
            with zipfile.ZipFile(archive) as native_package:
                for asset in details.get('runtime',{}):
                    if not asset.endswith('.dll'): continue
                    expected = native_package.read(asset)
                    actual = consumer/'bin/Debug/net10.0'/Path(asset).name
                    assert actual.read_bytes()==expected, 'Executed SDK runtime differs from native package'
                    executed[actual.name]={'package':package,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                                           'asset':asset,'sha256':hashlib.sha256(expected).hexdigest()}
        # Lock preparation intentionally writes one new maintained lock; no other
        # source may change while this native execution is running.
        assert basis == {file.relative_to(ROOT).as_posix():hashlib.sha256(file.read_bytes()).hexdigest()
                         for file in files if file.is_file() and (not args.prepare_lock or file.name!='packages.lock.json')}
        result.update(status='passed',native=native,sourceSha256=basis,executedRuntime=executed,
                      lockSha256=hashlib.sha256((consumer/'packages.lock.json').read_bytes()).hexdigest(),
                      fixtureAssemblySha256=hashlib.sha256((consumer/'bin/Debug/net10.0/OcrOperation.dll').read_bytes()).hexdigest())
        return 0
    except BaseException as error:
        result.update(status='failed',diagnostic=str(error))
        raise
    finally:
        (evidence/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('Offline native OCR SDK evidence: '+str(evidence/'results.json'))


if __name__=='__main__':
    raise SystemExit(main())
