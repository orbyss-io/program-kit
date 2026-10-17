"""Explicit public-package preparation for the bounded native OCR adapter; no provider call."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile

from provider_operation import require, canonical, sha, local, load, root_path
import asset_sources


def sources(root):
    installed = root/'.specify/extensions/program-kit-dotnet'
    extension = installed if installed.is_dir() else Path(__file__).resolve().parents[2]/'program-kit-dotnet'
    example = extension/'references/examples/ocr-operation'
    require(asset_sources.tree(example), 'co-installed native OCR reference is unavailable')
    return example, extension/'templates/dotnet/files'


def prepared_sources(example):
    return {name:sha(data) for name,data in asset_sources.tree(example).items()}


def mechanisms():
    return {name:sha(Path(__file__).with_name(name).read_bytes()) for name in
            ('provider_operation.py','provider_operation_authority.py','provider_operation_prepare.py','provider_operation_execute.py','asset_sources.py')
            if Path(__file__).with_name(name).is_file()}


def prepare(root):
    """Build only owned reference sources under neutral MSBuild policy and run recording cases."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from owned_scratch import owned_scratch, native_path
    import device_toolchain as device
    root=root_path(root)
    example,template=sources(root)
    original=prepared_sources(example)
    original_mechanisms=mechanisms()
    require('packages.lock.json' in original, 'optional adapter lock needs maintainer preparation')
    pin=root/'global.json' if (root/'global.json').is_file() else template/'global.json'
    sdk=load(pin)
    expected=sdk.get('sdk',{}).get('version')
    require(isinstance(expected,str) and expected, 'selected native SDK pin is unavailable')
    dotnet=device.executable('dotnet',root)
    require(dotnet is not None, device.render(device.diagnostic('dotnet',expected,str(pin),None,None,root)))
    output=local(root,'artifacts/provider-operations/adapters/'+uuid.uuid4().hex)
    output.mkdir(parents=True)
    result={'schemaVersion':1,'kind':'program-kit-ocr-native-preparation','status':'running',
            'sourceSha256':original,'mechanismSha256':original_mechanisms,'sdk':sdk,'executable':{'path':str(dotnet),'sha256':sha(dotnet.read_bytes())},
            'providerCalls':0,'modelCalls':0,'scope':'Owned native SDK adapter build and recording HTTP only',
            'steps':[]}
    env=dict(os.environ, NUGET_PACKAGES=native_path(output/'nuget'),NUGET_HTTP_CACHE_PATH=native_path(output/'http'),
             DOTNET_CLI_HOME=native_path(output/'dotnet-home'),MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_USE_MSBUILD_SERVER='0',PYTHONUTF8='1')
    env.pop('PROGRAMKIT_OCR_API_KEY',None)
    def run(label,arguments,cwd):
        observed=subprocess.run(list(map(str,arguments)),cwd=native_path(cwd),env=env,capture_output=True,
                                text=True,encoding='utf-8',timeout=180)
        for stream in ('stdout','stderr'):
            (output/(label+'.'+stream+'.log')).write_text(getattr(observed,stream),encoding='utf-8')
        result['steps'].append({'id':label,'command':list(map(str,arguments)),'exitCode':observed.returncode})
        require(observed.returncode==0,'native adapter preparation failed: '+str(output/(label+'.stdout.log')))
        return observed.stdout
    try:
        with owned_scratch(root,'validation-fixture') as staging:
            for name,data in asset_sources.tree(example).items():
                require('/' not in name,'unqualified nested native OCR example')
                (staging/name).write_bytes(data)
            (staging/'global.json').write_bytes(pin.read_bytes())
            # This auxiliary project never imports consumer build/CPM hooks.
            for name in ('Directory.Build.props','Directory.Build.targets','Directory.Packages.props'):
                (staging/name).write_text('<Project/>')
            (staging/'NuGet.config').write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
            require(run('sdk',[dotnet,'--version'],staging).strip()==expected,
                    device.render(device.diagnostic('dotnet',expected,str(pin),None,str(dotnet),root)))
            result['runtimeListSha256']=sha(run('runtimes',[dotnet,'--list-runtimes'],staging).strip().encode())
            run('restore',[dotnet,'restore','OcrOperation.csproj','--locked-mode','--configfile','NuGet.config',
                           '--disable-build-servers','-p:ManagePackageVersionsCentrally=false'],staging)
            run('build',[dotnet,'build','OcrOperation.csproj','--no-restore','--disable-build-servers','-m:1',
                         '-p:ManagePackageVersionsCentrally=false'],staging)
            native=json.loads(run('recording',[dotnet,native_path(staging/'bin/Debug/net10.0/OcrOperation.dll'),'recording-tests'],staging))
            required=json.loads(asset_sources.read(example/'required-cases.json'))
            require(native['status']=='passed' and native['providerCalls']==0 and native['modelCalls']==0
                    and native['providerAcceptance'] is False and len(native['cases'])==len(set(native['cases']))
                    and set(native['cases'])==set(required),'required native recording cases are incomplete')
            assets=load(staging/'obj/project.assets.json')['targets']['net10.0']
            runtime={}
            for package,details in assets.items():
                identity,version=package.split('/')
                archive=Path(env['NUGET_PACKAGES'])/identity.lower()/version/(identity.lower()+'.'+version+'.nupkg')
                with zipfile.ZipFile(archive) as contents:
                    for asset in details.get('runtime',{}):
                        if not asset.endswith('.dll'):continue
                        actual=staging/'bin/Debug/net10.0'/Path(asset).name
                        require(actual.read_bytes()==contents.read(asset),'native adapter dependency differs from restored archive')
                        runtime[actual.name]={'package':package,'archiveSha256':sha(archive.read_bytes()),'sha256':sha(actual.read_bytes())}
            payload=output/'payload';payload.mkdir()
            for file in (staging/'bin/Debug/net10.0').iterdir():
                require(file.is_file(),'unqualified nested native adapter output')
                shutil.copyfile(file,payload/file.name)
            result.update(native=native,executedRuntime=runtime,
                          payloadSha256={file.name:sha(file.read_bytes()) for file in payload.iterdir()},
                          pinPath=str(pin),pinSha256=sha(pin.read_bytes()))
        require(prepared_sources(example)==original,'native adapter sources changed during preparation')
        require(mechanisms()==original_mechanisms,'operation mechanisms changed during preparation')
        result['status']='passed'
    except BaseException as error:
        result.update(status='failed',diagnostic=str(error))
        raise
    finally:
        (output/'receipt.json').write_bytes(canonical(result))
    return (output/'receipt.json').relative_to(root).as_posix()


def verify(root, relative, expected_sha256):
    """Read-only readiness; execution never restores, builds or acquires tools."""
    root=root_path(root)
    path=local(root,relative)
    require(sha(path.read_bytes())==expected_sha256,'native adapter preparation record changed')
    value=load(path)
    require(type(value.get('schemaVersion')) is int and value['schemaVersion']==1 and value.get('kind')=='program-kit-ocr-native-preparation'
            and value.get('status')=='passed' and value.get('providerCalls')==0 and value.get('modelCalls')==0,'native adapter preparation is incomplete')
    example,_=sources(root)
    require(value['sourceSha256']==prepared_sources(example),'native adapter sources changed; explicitly prepare current inputs again')
    require(value['mechanismSha256']==mechanisms(),'operation admission/execution mechanism changed; explicitly prepare current inputs again')
    required=json.loads(asset_sources.read(example/'required-cases.json'))
    native=value['native']
    require(native['status']=='passed' and native['providerCalls']==0 and native['modelCalls']==0 and native['providerAcceptance'] is False
            and len(native['cases'])==len(set(native['cases'])) and set(native['cases'])==set(required),
            'native adapter preparation lacks its complete named recording-case inventory')
    binary=path.parent/'payload'
    require({file.name for file in binary.iterdir()}==set(value['payloadSha256']), 'native adapter payload has missing or extra files')
    for name,digest in value['payloadSha256'].items():
        require('/' not in name and '\\' not in name and name not in ('.','..'),'invalid native adapter payload identity')
        file=local(root,(binary/name).relative_to(root).as_posix())
        require(file.is_file() and sha(file.read_bytes())==digest,'native adapter payload changed')
    executable=Path(value['executable']['path'])
    from dotnet_adapter import bootstrap
    bootstrap()
    import device_toolchain as device
    selected=device.executable('dotnet',root)
    require(executable.is_absolute() and selected is not None and executable.resolve()==selected.resolve()
            and executable.is_file() and sha(executable.read_bytes())==value['executable']['sha256'],
            'native runtime executable changed; explicit readiness/preparation is required')
    observed=device.probe([str(executable),'--list-runtimes'],root)
    require(observed is not None and sha(observed.encode())==value['runtimeListSha256'],
            'prepared native runtime set changed or is unavailable; explicitly prepare/read readiness before dependent execution')
    return value,executable,binary/'OcrOperation.dll'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--initialize-account',action='store_true',help='Human terminal only: initialize one original retained resource account')
    parser.add_argument('--resource')
    parser.add_argument('--ceiling-micro-usd',type=int)
    parser.add_argument('--historical-reservations',help='Contained JSON array of original path/hash/reservationMicroUsd records; use [] only after reviewing existing history')
    args=parser.parse_args()
    if args.initialize_account:
        from provider_operation import Account
        require(sys.stdin.isatty() and sys.stdout.isatty(),'original provider account initialization is human terminal owned')
        require(args.resource and args.ceiling_micro_usd and args.historical_reservations,
                'account initialization requires resource, original aggregate ceiling and explicit historical mappings')
        root=args.repository.resolve()
        history=load(local(root,args.historical_reservations))
        print(json.dumps({'resource':args.resource,'ceilingMicroUsd':args.ceiling_micro_usd,'historicalReservations':history},indent=2))
        expected='INITIALIZE ORIGINAL OCR ACCOUNT '+args.resource+' CEILING '+str(args.ceiling_micro_usd)+' MICROUSD'
        print(expected)
        require(input('Review all existing attempts and type the complete line: ')==expected,'original account confirmation missing')
        print(Account(root,args.resource).initialize(args.ceiling_micro_usd,history))
        return 0
    require(not (args.resource or args.ceiling_micro_usd or args.historical_reservations),'account inputs require explicit account initialization')
    print(prepare(args.repository))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
