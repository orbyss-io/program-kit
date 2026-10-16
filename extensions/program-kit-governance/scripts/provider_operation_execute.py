"""One guarded native OCR action; execution never prepares tools or renews authority."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import threading
import time
import uuid

from provider_operation import Account, contract, canonical, sha, local, require
from provider_operation_prepare import verify as verify_adapter


MAX_STREAM = 262144


def runtime_environment(execution, credential):
    """Only this native provider process receives its one scoped credential.

    This is a provider transport's explicit environment, not consumer bootstrap
    or coding-worker sandbox setup. No agent process is started here.
    """
    allowed = {'PATH','SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','HOME','USERPROFILE',
               'LOCALAPPDATA','APPDATA','DOTNET_ROOT','DOTNET_ROOT_X64','DOTNET_ROOT_X86','LANG','LC_ALL',
               'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy'}
    environment = {name:value for name,value in os.environ.items() if name in allowed}
    environment.update(PYTHONUTF8='1',DOTNET_EnableDiagnostics='0',DOTNET_CLI_TELEMETRY_OPTOUT='1')
    if execution=='provider':environment['PROGRAMKIT_OCR_WORKER_KEY']=credential
    return environment


def invoke(account, identity, value, executable, dll, action, timeout_ms, *, execution, credential=None,
           handle=None, recording_outcome=None,deadline_monotonic):
    """Consume one owned ticket and retain available handles before sealing outcome."""
    from dotnet_adapter import bootstrap
    bootstrap()
    from owned_scratch import native_path
    require(execution in ('recording','provider') and (execution=='recording' or recording_outcome is None),
            'recording controls cannot enter provider execution')
    nonce=str(uuid.uuid4())
    directory=local(account.root,(account.directory/'tickets'/identity).relative_to(account.root).as_posix())
    directory.mkdir(parents=True,exist_ok=True)
    local(account.root,directory.relative_to(account.root).as_posix())
    ticket=directory/(nonce+'.json')
    timeout_ms=min(timeout_ms,value['limits']['timeoutMilliseconds' if action=='submit' else 'pollTimeoutMilliseconds'])
    timeout_ms=min(timeout_ms,int((deadline_monotonic-time.monotonic())*1000))
    if timeout_ms<=0:
        return {'status':'unavailable','responseSha256':None},{'started':False,'status':'unavailable',
                'timedOut':True,'streamsDrained':True,'events':[],'scope':'Expired before owned process launch'},None
    deadline=min(value['submitBefore' if action=='submit' else 'recoverBefore'],time.time()+timeout_ms/1000)
    body={'schemaVersion':1,'kind':'program-kit-ocr-worker-ticket','execution':execution,'attempt':identity,'nonce':nonce,
          'originalTicketPath':native_path(ticket),'action':action,'endpoint':value['endpoint'],
          'fixturePath':native_path(local(account.root,value['fixture']['path'])) if action=='submit' else None,
          'fixtureSha256':value['fixture']['sha256'] if action=='submit' else None,
          'maximumInputBytes':value['limits']['maximumInputBytes'],'maximumResponseBytes':value['limits']['maximumResponseBytes'],
          'timeoutMilliseconds':max(1,int(timeout_ms)),'deadlineUnixMilliseconds':int(deadline*1000),
          'resultHandle':handle,'recordingOutcome':recording_outcome}
    with ticket.open('xb') as stream:
        stream.write(canonical(body));stream.flush();os.fsync(stream.fileno())
    ticket_sha=sha(ticket.read_bytes())
    logs=directory/(nonce+'-streams');logs.mkdir()
    command=[str(executable),native_path(dll),'ticket',native_path(ticket),ticket_sha]
    try:
        process=subprocess.Popen(command,cwd=native_path(dll.parent),env=runtime_environment(execution,credential),
                                 stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    except BaseException as error:
        (logs/'process.json').write_bytes(canonical({'started':False,'command':command,'status':'unavailable',
                'errorType':type(error).__name__,'ticketSha256':ticket_sha,'scope':'No owned worker was started'}))
        raise
    observed={'started':True,'command':command,'pid':process.pid,'ticketSha256':ticket_sha,'execution':execution,'action':action,
              'timedOut':False,'streams':{},'events':[],'providerAcceptance':False}
    buffers={'stdout':bytearray(),'stderr':bytearray()}
    hashes={'stdout':hashlib.sha256(),'stderr':hashlib.sha256()}
    counts={'stdout':0,'stderr':0}
    errors=[]
    unsafe=threading.Event()
    def line(payload):
        require(len(payload)<=16384,'native control line exceeds its bound')
        def unique(pairs):
            result={}
            for key,item in pairs:
                require(key not in result,'duplicate native control field')
                result[key]=item
            return result
        event=json.loads(payload.decode('utf-8'),object_pairs_hook=unique)
        require(isinstance(event,dict) and len(observed['events'])<16,'unqualified native control output')
        kind=event.get('event')
        if kind=='handle':
            require(action=='submit' and set(event)=={'event','handle'},'unqualified handle output')
            account.retain_handle(identity,event['handle'])
        elif kind=='outcome':
            require(set(event)<= {'event','status','responseSha256','errorType'} and event.get('status') in
                    ({'acknowledged','unknown','unavailable'} if action=='submit' else
                     {'unknown'} if action=='delete' else {'unknown','running','succeeded','failed','absent'}), 'unqualified native outcome')
            require(event.get('responseSha256') is None or action=='poll' and event['status']=='succeeded'
                    and isinstance(event['responseSha256'],str) and re.fullmatch('[0-9a-f]{64}',event['responseSha256']),
                    'unqualified private result identity')
            require('errorType' not in event or isinstance(event['errorType'],str)
                    and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,127}',event['errorType']), 'unqualified native diagnostic')
        elif kind=='recording-transport':
            require(execution=='recording' and set(event)=={'event','method'} and event['method']==
                    {'submit':'POST','poll':'GET','delete':'DELETE'}[action],'unexpected native transport operation')
        else:raise ValueError('PKO001 unknown native control event')
        observed['events'].append(event)
    def drain(name,stream):
        pending=bytearray()
        try:
            while True:
                chunk=stream.read1(4096)
                if not chunk:break
                hashes[name].update(chunk);counts[name]+=len(chunk)
                if counts[name]>MAX_STREAM:
                    unsafe.set();continue
                buffers[name].extend(chunk)
                if name=='stdout':
                    pending.extend(chunk)
                    require(len(pending)<=16384,'native control line exceeds its bound')
                    while b'\n' in pending:
                        data,_,rest=pending.partition(b'\n');pending=bytearray(rest)
                        if data.strip():line(data.rstrip(b'\r'))
            if name=='stdout' and pending.strip():line(bytes(pending))
        except BaseException as error:
            errors.append(type(error).__name__);unsafe.set()
        finally:stream.close()
    threads=[threading.Thread(target=drain,args=(name,getattr(process,name)),daemon=True) for name in ('stdout','stderr')]
    for thread in threads:thread.start()
    limit=deadline_monotonic+2
    interruption=None
    try:
        while process.poll() is None:
            if unsafe.is_set() or time.monotonic()>=limit:
                observed['timedOut']=time.monotonic()>=limit
                process.kill()  # Exact owned native process handle; no liveness signalling probe.
                break
            time.sleep(.01)
        observed['exitCode']=process.wait(timeout=10)
    except BaseException as error:
        interruption=error
        observed['interruptionType']=type(error).__name__
        observed['operatorInterruptionObserved']=isinstance(error,KeyboardInterrupt)
        try:
            if process.poll() is None:process.kill()
            observed['exitCode']=process.wait(timeout=10)
        except BaseException as cleanup_error:
            observed['cleanupErrorType']=type(cleanup_error).__name__
    finally:
        observed['ownedProcessStopped']=process.poll() is not None
        for thread in threads:thread.join(timeout=6)
        observed['streamsDrained']=all(not thread.is_alive() for thread in threads)
        observed['protocolErrors']=errors
        for name in ('stdout','stderr'):
            raw=bytes(buffers[name])
            replacements=0
            if credential:
                key=credential.encode();replacements=raw.count(key);raw=raw.replace(key,b'[REDACTED]')
            path=logs/(name+'.log');path.write_bytes(raw)
            observed['streams'][name]={'path':path.relative_to(account.root).as_posix(),'rawBytes':counts[name],
                                      'rawSha256':hashes[name].hexdigest(),'retainedSha256':sha(raw),'redactions':replacements,
                                      'truncated':counts[name]>MAX_STREAM}
    outcomes=[event for event in observed['events'] if event.get('event')=='outcome']
    complete=observed.get('exitCode')==0 and observed['ownedProcessStopped'] and observed['streamsDrained'] and not unsafe.is_set() and len(outcomes)==1
    if time.monotonic()>deadline_monotonic and outcomes and outcomes[0].get('status')!='unknown':complete=False
    result=outcomes[0] if complete else {'status':'unknown','responseSha256':None}
    if execution=='recording':
        methods=[event['method'] for event in observed['events'] if event.get('event')=='recording-transport']
        require(len(methods)<=1,'native adapter dispatched more than its one scoped transport action')
    observed['status']=result['status']
    (logs/'process.json').write_bytes(canonical(observed))
    if interruption is not None:raise interruption
    return result,observed,(ticket.with_name(ticket.name+'.result') if result.get('responseSha256') else None)


def run(root, relative, authorization, prerequisite, recipe, *, execution='recording',recording_outcome=None):
    started=time.monotonic()
    root=Path(root).resolve()
    prepared=contract(root,relative)
    adapter=prepared['value']['adapterPreparation']
    _,executable,dll=verify_adapter(root,adapter['path'],adapter['sha256'])
    require(execution in ('recording','provider') and (execution=='recording' or recording_outcome is None), 'invalid execution mode')
    credential=None
    if execution=='provider':
        # Read only after the exact native and separate human authorization check.
        from provider_operation import native_admission
        from provider_operation_authority import read
        native=native_admission(root,prepared,prerequisite,recipe)
        read(root,authorization,prepared,native,execution)
        credential=os.environ.get(prepared['value']['credentialRef'])
        require(isinstance(credential,str) and 0<len(credential)<=8192 and '\r' not in credential and '\n' not in credential,
                'the exact scoped OCR credential is unavailable; complete its human-owned provider preparation')
    account=Account(root,prepared['resource'])
    identity=account.reserve(prepared,prerequisite,recipe,authorization,execution=execution)
    value,remaining=account.dispatch_intent(identity)
    value['dispatchDeadlineMonotonic']=min(value['dispatchDeadlineMonotonic'],started+prepared['value']['limits']['timeoutMilliseconds']/1000)
    try:
        outcome,process,result=invoke(account,identity,value['value'],executable,dll,'submit',remaining,
                                      execution=execution,credential=credential,
                                      deadline_monotonic=value['dispatchDeadlineMonotonic'],
                                      recording_outcome=(recording_outcome or 'accepted') if execution=='recording' else None)
        status=outcome['status'] if outcome['status'] in ('acknowledged','unavailable') else 'unknown'
    except BaseException:
        account.submission_outcome(identity,'unknown')
        raise
    account.submission_outcome(identity,status)
    return {'attempt':identity,'status':status,'execution':execution,'process':process,'account':account.status(identity),
            'scope':'One OCR-only operation; no model, combined provider or application acceptance'}


def recover(root,resource,identity,action,*,recording_outcome=None):
    started=time.monotonic()
    account=Account(Path(root).resolve(),resource)
    current=account.status(identity)['events'][0]
    value=account.original(current)
    adapter=value['adapterPreparation']
    _,executable,dll=verify_adapter(account.root,adapter['path'],adapter['sha256'])
    execution=current['grant']['execution']
    require(execution=='recording' or recording_outcome is None,'recording controls cannot enter provider recovery')
    credential=None
    if execution=='provider':
        account.historical_admission(current)
        credential=os.environ.get(value['credentialRef'])
        require(isinstance(credential,str) and credential,'the original scoped OCR credential is required for bounded recovery')
    value,handle,token=account.recovery_intent(identity,action)
    value['_recoveryDeadlineMonotonic']=min(value['_recoveryDeadlineMonotonic'],started+value['limits']['pollTimeoutMilliseconds']/1000)
    try:
        outcome,process,result=invoke(account,identity,value,executable,dll,action,value['limits']['pollTimeoutMilliseconds'],
                                      execution=execution,credential=credential,handle=handle,
                                      deadline_monotonic=value['_recoveryDeadlineMonotonic'],
                                      recording_outcome=(recording_outcome or ('running' if action=='poll' else 'delete-accepted')) if execution=='recording' else None)
        status=outcome['status'] if action=='poll' and outcome['status'] in ('running','succeeded','failed','absent') else 'unknown'
        if result is not None:
            require(result.is_file() and result.stat().st_size<=value['limits']['maximumResponseBytes'],
                    'owned private OCR result is missing or exceeds its bound')
            with result.open('rb') as stream:
                payload=stream.read(value['limits']['maximumResponseBytes']+1)
            require(len(payload)<=value['limits']['maximumResponseBytes'] and sha(payload)==outcome['responseSha256'],
                    'owned private OCR result changed')
    except BaseException:
        account.recovery_outcome(identity,token,'unknown')
        raise
    account.recovery_outcome(identity,token,status,outcome.get('responseSha256'))
    return {'attempt':identity,'status':status,'execution':execution,'process':process,
            'privateResult':result.relative_to(account.root).as_posix() if result else None,
            'account':account.status(identity),'scope':'Original bounded recovery only; no new submission or model authority'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,required=True)
    sub=parser.add_subparsers(dest='mode',required=True)
    start=sub.add_parser('run');start.add_argument('--contract',required=True);start.add_argument('--authorization',required=True)
    start.add_argument('--prerequisite',required=True);start.add_argument('--recipe',required=True)
    start.add_argument('--execution',choices=('recording','provider'),default='recording')
    again=sub.add_parser('recover');again.add_argument('--resource',required=True);again.add_argument('--attempt',required=True)
    again.add_argument('--action',choices=('poll','delete'),required=True)
    args=parser.parse_args()
    if args.mode=='run':value=run(args.repository,args.contract,args.authorization,args.prerequisite,args.recipe,execution=args.execution)
    else:value=recover(args.repository,args.resource,args.attempt,args.action)
    print(json.dumps(value,indent=2))
    return 0 if value['status'] in ('acknowledged','running','succeeded','absent') else 2


if __name__=='__main__':
    raise SystemExit(main())
