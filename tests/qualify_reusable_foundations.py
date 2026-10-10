"""Fresh disposable qualification of generated compositions; no live consumers are modified.

Cold means fresh consumer NuGet/npm acquisition caches and isolated browser
downloads. Preinstalled SDK and immutable Docker images are reported explicitly,
never described as a cold machine. Prepared runs reuse the consumer's caches.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'extensions/program-kit-dotnet/scripts'
sys.path.insert(0,str(SCRIPTS))
import foundation_composition as composition
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
from compatibility_process import run


def contract_tests():
    """Failure-contract tests of maintained orchestration; these claim no runtime readiness."""
    import importlib.util
    import http.server
    import threading
    path=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/foundation_qualification.py'
    spec=importlib.util.spec_from_file_location('qualification_contract_test',path)
    adapter=importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    evidence=ROOT/'artifacts/tests/reusable-foundations'/('contracts-'+uuid.uuid4().hex[:16])
    evidence.mkdir(parents=True)
    checks=[]
    def rejected(name,action):
        try: action()
        except ValueError: checks.append(name); return
        raise AssertionError('Invalid readiness evidence admitted: '+name)
    for variant in sorted(composition.VARIANTS):
        selected=adapter.setup_contract({'compositionId':variant})
        expected={'host-activation','bff-cookie','keycloak'} | ({'postgresql'} if variant.endswith('postgresql') else set())
        assert set(selected['tests']['capabilities'])==expected
        assert {row['stage'] for row in selected['setup']['steps']}=={'restore','build','services'}
        assert all(row['result']['cases']==adapter.CASES[row['capability']] for row in selected['tests']['commands'])
    checks.append('finite-supported-compositions-use-authoritative-nonempty-maintained-cases')
    platform={'status':'passed','cases':{case:True for values in adapter.CASES.values() for case in values},'productAcceptance':False}
    def failing_product(): raise ValueError('Expected application assertion failure')
    adapter.product_outcome(platform,failing_product)
    assert platform['status']=='passed' and all(platform['cases'].values()) and platform['productAcceptance'] is False
    assert platform['productPhase']['failure']=='application-proving-failed'
    checks.append('application-failure-remains-visible-without-erasing-platform-cases')
    platform['productAcceptance']=True
    adapter.product_outcome(platform,failing_product,phase='retained-product-after-provider-and-host-restart')
    assert platform['status']=='passed' and all(platform['cases'].values()) and platform['productAcceptance'] is False
    assert platform['productPhase']['phase']=='retained-product-after-provider-and-host-restart'
    checks.append('retained-application-failure-does-not-erase-platform-restart')
    rejected('live-origin-executable-refused',lambda:adapter.local_origin('https://live.example'))
    rejected('selected-configurable-owner-unobserved-refused',lambda:adapter.activated_settings(evidence,
             {'tests':{'capabilities':['host-activation']}},{},{'owners':[]}))
    root=evidence/'consumer'; directory=root/'artifacts/tests/runs/current'; directory.mkdir(parents=True)
    bundle=root/'artifacts/runtime'; bundle.mkdir(); (bundle/'shells.json').write_text('{}')
    selected={'runtimeStage':'artifacts/runtime','tests':{'capabilities':['bff-cookie']}}
    rejected('no-activation-evidence-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result={'status':'failed','cleanupComplete':True,'bundleInputs':adapter.bundle_hashes(root,selected),'cases':{adapter.CASES['bff-cookie'][0]:True}}
    write(directory/'integration.json',result)
    rejected('failed-evidence-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['status']='passed'; result['cleanupComplete']=False; write(directory/'integration.json',result)
    rejected('incomplete-cleanup-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['cleanupComplete']=True; result['bundleInputs']={}; write(directory/'integration.json',result)
    rejected('changed-staged-inputs-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    result['bundleInputs']=adapter.bundle_hashes(root,selected); result['cases']={}; write(directory/'integration.json',result)
    rejected('missing-actual-case-refused',lambda:adapter.check(root,selected,'bff-cookie',directory))
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'local helper contract')
        def log_message(self,*_): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever); thread.start()
    try: assert adapter.request('http://127.0.0.1:'+str(server.server_port),'/')[0]==200
    finally: server.shutdown(); server.server_close(); thread.join()
    checks.append('native-http-readiness-client-works-and-closes')
    cache_home=evidence/'cache-inventory-fixture'
    for platform,expected in (('win32',cache_home/'AppData/Local/ms-playwright'),
                              ('linux',cache_home/'.cache/ms-playwright'),
                              ('darwin',cache_home/'Library/Caches/ms-playwright')):
        observed=browser_cache_inventory(environment={},platform=platform,home=cache_home)
        assert observed['cachePath']==str(expected) and not observed['directoryExists']
        assert observed['observedDirectories']==[] and observed['browserReadinessEstablished'] is False
    explicit=cache_home/'explicit'; (explicit/'chromium-fixture').mkdir(parents=True)
    (explicit/'marker.txt').write_text('a file is not an installed browser')
    observed=browser_cache_inventory(environment={'PLAYWRIGHT_BROWSERS_PATH':str(explicit)},platform='linux',home=cache_home)
    assert observed['cacheSource']=='PLAYWRIGHT_BROWSERS_PATH' and observed['observedDirectories']==['chromium-fixture']
    assert observed['browserReadinessEstablished'] is False
    for platform,key in (('win32','LOCALAPPDATA'),('linux','XDG_CACHE_HOME')):
        observed=browser_cache_inventory(environment={key:str(cache_home/'override')},platform=platform,home=cache_home)
        assert observed['cachePath']==str(cache_home/'override/ms-playwright')
    observed=browser_cache_inventory(environment={'PLAYWRIGHT_BROWSERS_PATH':'0'},platform='linux',home=cache_home)
    assert observed['cachePath'] is None and not observed['directoryExists'] and not observed['browserReadinessEstablished']
    checks.append('portable-preexisting-browser-cache-inventory-never-claims-readiness')
    # Exercise the actual maintained setup supervisor, with restore deliberately
    # failing before build/services; neither Docker nor a package manager runs.
    child=evidence/'failed-readiness-child'; child.mkdir()
    setup=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/foundation_setup.py'
    secret='qualification-diagnostic-secret-must-never-appear'
    untouched=child/'services-must-not-run'
    child_selected={'compositionId':'foundation-bff-keycloak','runtimeDirectory':'.',
        'setup':{'steps':[
            {'stage':'restore','command':[sys.executable,'-c','import sys; sys.exit(17)']},
            {'stage':'build','command':[sys.executable,'-c','raise AssertionError("build must not run")']},
            {'stage':'services','command':[sys.executable,'-c','from pathlib import Path; Path('+repr(str(untouched))+').touch()']} ]},
        'tests':{'capabilities':['host-activation','bff-cookie','keycloak'],'commands':[
            {'id':capability,'capability':capability,'command':[sys.executable,'-c','raise AssertionError("check must not run")'],
             'result':{'path':'artifacts/'+capability+'.xml','format':'junit','cases':['not-executed']}}
            for capability in ('host-activation','bff-cookie','keycloak')]}}
    shutil.copy2(ROOT/'extensions/program-kit-governance/scripts/compatibility_process.py',child/'foundation_process.py')
    write(child/'selected.json',child_selected)
    script=child/'fail_setup.py'
    script.write_text('import importlib.util,json,sys\nfrom pathlib import Path\n'
        +'sys.path.insert(0,'+repr(str(setup.parent))+')\n'
        +'spec=importlib.util.spec_from_file_location("actual_setup",'+repr(str(setup))+')\n'
        +'module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n'
        +'print('+repr(secret)+',file=sys.stderr)\n'
        +'try: module.execute(Path.cwd(),json.loads(Path("selected.json").read_text()))\n'
        +'except ValueError: sys.exit(2)\n',encoding='utf-8')
    try: command([sys.executable,str(script)],child,evidence/'failed-readiness-command',timeout=30,readiness=True)
    except ValueError as error:
        actual=str(error)
        assert 'readiness stage=restore stepExit=17 code=PKF003 outerExit=2;' in actual
        assert secret not in actual and not untouched.exists()
    else: raise AssertionError('Actual failed setup child was concealed')
    checks.append('actual-maintained-restore-failure-classified-without-service-start-or-stream-export')
    receipt=next((child/'artifacts/tests/runs').glob('foundation-*/result.json'))
    original=json.loads(receipt.read_text())
    assert readiness_failure(child,{receipt})=='stage=unknown stepExit=unknown code=unknown'
    checks.append('older-readiness-receipt-cannot-classify-this-command')
    for raw_stage,expected in (('build','build'),('services','services'),('host-activation','check'),
                               ('bff-cookie','check'),('keycloak','check'),('postgresql','check')):
        value={**original,'steps':[{'stage':raw_stage,'exitCode':19}], 'failure':'PKF004 '+secret}
        write(receipt,value)
        assert readiness_failure(child,set())=='stage='+expected+' stepExit=19 code=PKF004'+(' checkpoint=integration-absent childExit=unknown authentication=absent' if expected=='check' else '')
    checks.append('only-known-stage-enums-and-known-error-code-prefixes-projected')
    attacks=[None, [], {'schemaVersion':True}, {**original,'status':secret},
             {**original,'steps':secret}, {**original,'steps':[secret]},
             {**original,'steps':[{'stage':secret,'exitCode':secret}],'failure':secret},
             {**original,'steps':[{'stage':secret,'exitCode':True}],'failure':'PKF003-'+secret},
             {**original,'steps':[{'stage':secret,'exitCode':4294967296}],'failure':'PKF999 '+secret},
             {**original,'steps':[{'stage':secret,'exitCode':-2147483649}],'failure':'prefix PKF003 '+secret}]
    for value in attacks:
        write(receipt,value)
        assert readiness_failure(child,set())=='stage=unknown stepExit=unknown code=unknown'
    receipt.write_text(' '+secret*4000,encoding='utf-8')
    assert readiness_failure(child,set())=='stage=unknown stepExit=unknown code=unknown'
    receipt.write_text('{malformed '+secret,encoding='utf-8')
    assert readiness_failure(child,set())=='stage=unknown stepExit=unknown code=unknown'
    write(receipt,original)
    process=receipt.parent/'command-01/process.json'
    value={**original,'steps':[{'stage':'restore','status':'running'}]}
    write(receipt,value)
    assert readiness_failure(child,set())=='stage=restore stepExit=17 code=PKF003'
    write(process,{'exitCode':secret})
    assert readiness_failure(child,set())=='stage=restore stepExit=unknown code=PKF003'
    write(process,[])
    assert readiness_failure(child,set())=='stage=unknown stepExit=unknown code=unknown'
    checks.append('malformed-and-injected-metadata-never-forwards-secret-values')
    write(receipt,original)
    extra=receipt.parent.parent/'foundation-ambiguous/result.json'; write(extra,original)
    assert readiness_failure(child,set())=='stage=unknown stepExit=unknown code=unknown'
    checks.append('ambiguous-current-readiness-receipts-fail-closed')
    extra.unlink()
    value={**original,'steps':[{'stage':'host-activation','exitCode':2}],'failure':'PKF003 '+secret}
    write(receipt,value)
    prefix='stage=check stepExit=2 code=PKF003 '
    integration=receipt.parent/'integration.json'
    child_process=receipt.parent/('process-'+'a'*32)/'process.json'
    write(child_process,{'status':'failed','exitCode':29,'command':[secret],'environment':{'TOKEN':secret}})
    assert readiness_failure(child,set())==prefix+'checkpoint=integration-absent childExit=29'+' authentication=absent'
    cases={}
    observed={'schemaVersion':1,'status':'failed','cases':cases,'failure':secret,'timings':{},'runtimeTransport':[]}
    for name,add in [('before-issuer-check',()),('identity-ready',('Foundation.public_issuer_private_backchannel',)),
                     ('activated',('Foundation.actual_selected_feature_activation','Foundation.actual_bound_effective_settings')),
                     ('authenticated',('Foundation.maintained_bff_cookie',)),('provider-restarted',('Foundation.provider_connectivity_restart',))]:
        cases.update({case:True for case in add}); write(integration,observed)
        label=readiness_failure(child,set())
        assert label==prefix+'checkpoint='+name+' childExit=29 authentication=absent' and secret not in label
    observed['cases']={'Foundation.public_issuer_private_backchannel':True}
    observed['runtimeTransport']=[{'phase':'initial','before':{'byteIdentityVerified':True,'sourceInputs':{secret:secret}}}]
    write(integration,observed)
    assert readiness_failure(child,set())==prefix+'checkpoint=host-copied childExit=29'+' authentication=absent'
    observed['timings']={'hostReadinessSeconds':1.234}; write(integration,observed)
    assert readiness_failure(child,set())==prefix+'checkpoint=host-ready childExit=29'+' authentication=absent'
    checks.append('only-fixed-integration-checkpoints-and-numeric-child-exits-projected')
    assert readiness_failure(child,set(),{integration})==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    assert readiness_failure(child,set(),{child_process})==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    checks.append('previous-child-metadata-cannot-classify-new-readiness')
    for invalid in ([],{**observed,'schemaVersion':True},{**observed,'cases':{secret:True}},
                    {**observed,'cases':{'Foundation.maintained_bff_cookie':True}},
                    {**observed,'runtimeTransport':[{'phase':secret}]},
                    {**observed,'timings':{'hostReadinessSeconds':secret}},
                    {**observed,'cases':{'Foundation.public_issuer_private_backchannel':secret}}):
        write(integration,invalid)
        assert readiness_failure(child,set())==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    for raw in ('{malformed '+secret,' '+secret*4000):
        integration.write_text(raw,encoding='utf-8')
        assert readiness_failure(child,set())==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    write(integration,observed)
    for code in (True,secret,4294967296,-2147483649):
        write(child_process,{'status':'failed','exitCode':code,'failure':secret})
        assert readiness_failure(child,set())==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    write(child_process,{'status':'failed','exitCode':29})
    other=receipt.parent/('process-'+'b'*32)/'process.json'; write(other,{'status':'failed','exitCode':31})
    assert readiness_failure(child,set())==prefix+'checkpoint=host-ready childExit=unknown'+' authentication=absent'
    other.unlink()
    checks.append('malformed-oversized-injected-and-conflicting-child-metadata-fail-closed')
    crowded=[]
    for number in range(129):
        path=receipt.parent/('process-'+format(number,'032x'))/'process.json'
        write(path,{'status':'completed','exitCode':0}); crowded.append(path)
    assert readiness_failure(child,set())==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    for path in crowded:
        path.unlink(); path.parent.rmdir()
    checks.append('child-metadata-count-budget-fails-closed')
    # Parent directory traversal and symlink escapes are checked before any read.
    def confined(path):
        if path.resolve()!=path.absolute() or not path.resolve().is_relative_to(receipt.parent):
            raise ValueError('Invalid diagnostic metadata')
        return json.loads(path.read_text())
    outside=evidence/'outside-integration.json'; write(outside,observed)
    try:
        integration.unlink(); integration.symlink_to(outside)
    except OSError:
        from unittest.mock import patch
        write(integration,observed)
        original_resolve=Path.resolve
        def escaping_resolve(path,*args,**keywords):
            return outside if path==integration else original_resolve(path,*args,**keywords)
        with patch.object(Path,'resolve',escaping_resolve):
            assert readiness_failure(child,set())==prefix+'checkpoint=unknown childExit=unknown'+' authentication=absent'
    else:
        assert integration_failure(receipt.parent,confined,set())=='checkpoint=unknown childExit=unknown'
        integration.unlink(); write(integration,observed)
    checks.append('escaping-integration-metadata-never-enters-labels')
    # Real maintained child capture writes the same process metadata consumed above.
    fixture_path=ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/foundation_fixture.py'
    capture_spec=importlib.util.spec_from_file_location('integration_failure_capture',fixture_path)
    fixture=importlib.util.module_from_spec(capture_spec)
    prior_module=sys.modules.get('foundation_process')
    sys.modules['foundation_process']=sys.modules['compatibility_process']
    try: capture_spec.loader.exec_module(fixture)
    finally:
        if prior_module is None: sys.modules.pop('foundation_process')
        else: sys.modules['foundation_process']=prior_module
    actual=receipt.parent/('process-'+uuid.uuid4().hex)
    captured=fixture.captured([sys.executable,'-c','import sys; print('+repr(secret)+'); sys.exit(29)'],child,actual,timeout=30)
    assert captured['exitCode']==29 and captured['cleanupComplete'] and captured['logsDrained']
    assert readiness_failure(child,set())==prefix+'checkpoint=host-ready childExit=29'+' authentication=absent'
    checks.append('actual-maintained-failed-child-capture-produces-only-bounded-diagnostics')
    check_child=evidence/'failed-check-readiness-child'; check_child.mkdir()
    shutil.copy2(child/'foundation_process.py',check_child/'foundation_process.py')
    shutil.copy2(child/'fail_setup.py',check_child/'fail_setup.py')
    check_script=check_child/'fail_check.py'
    check_script.write_text('import importlib.util,json,sys,uuid\nfrom pathlib import Path\n'
        +'spec=importlib.util.spec_from_file_location("actual_fixture",'+repr(str(fixture_path))+')\n'
        +'module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n'
        +'directory=Path(sys.argv[1]); process=directory/("process-"+uuid.uuid4().hex)\n'
        +'module.captured([sys.executable,"-c",'+repr('import sys; print('+repr(secret)+'); sys.exit(29)')+'],Path.cwd(),process,timeout=30)\n'
        +'(directory/"integration.json").write_text('+repr(json.dumps({'schemaVersion':1,'status':'failed',
              'cases':{'Foundation.public_issuer_private_backchannel':True},'failure':secret,
              'command':[secret],'environment':{'TOKEN':secret}}))+',encoding="utf-8")\n'
        +'print('+repr(secret)+',file=sys.stderr); sys.exit(2)\n',encoding='utf-8')
    selected_check=json.loads(json.dumps(child_selected))
    for row in selected_check['setup']['steps']: row['command']=[sys.executable,'-c','pass']
    selected_check['tests']['commands'][0]['command']=[sys.executable,str(check_script),'{runDirectory}']
    write(check_child/'selected.json',selected_check)
    try: command([sys.executable,str(check_child/'fail_setup.py')],check_child,evidence/'failed-check-readiness-command',timeout=30,readiness=True)
    except ValueError as error:
        label=str(error)
        assert 'readiness stage=check stepExit=2 code=PKF003 checkpoint=identity-ready childExit=29 authentication=absent outerExit=2;' in label
        assert secret not in label
    else: raise AssertionError('Actual maintained check failure was concealed')
    checks.append('actual-maintained-check-failure-prints-checkpoint-without-child-prose-or-streams')
    injected=evidence/'injected-readiness-child'; injected.mkdir()
    injection={'schemaVersion':1,'kind':'foundation-readiness','status':'failed',
        'steps':[{'stage':secret,'exitCode':secret}],'failure':'PKF003-'+secret,
        'command':[secret],'environment':{'TOKEN':secret}}
    script=injected/'inject_metadata.py'
    script.write_text('import json,sys\nfrom pathlib import Path\n'
        +'path=Path("artifacts/tests/runs/foundation-injected/result.json"); path.parent.mkdir(parents=True)\n'
        +'path.write_text('+repr(json.dumps(injection))+',encoding="utf-8")\n'
        +'print('+repr(secret)+'); print('+repr(secret)+',file=sys.stderr); sys.exit(23)\n',encoding='utf-8')
    try: command([sys.executable,str(script)],injected,evidence/'injected-readiness-command',timeout=30,readiness=True)
    except ValueError as error:
        actual=str(error)
        assert 'readiness stage=unknown stepExit=unknown code=unknown outerExit=23;' in actual
        assert secret not in actual
    else: raise AssertionError('Injected failed child was concealed')
    checks.append('actual-child-streams-and-injected-metadata-cannot-enter-outer-failure-labels')
    # Controlled native children observe and write markers, without invoking npm
    # or a browser. Ambient acquisition folders must remain entirely untouched.
    cache_names=('PROGRAMKIT_NPM_CACHE','NPM_CONFIG_CACHE','PLAYWRIGHT_BROWSERS_PATH')
    parent={name:os.environ.get(name) for name in cache_names}
    sentinel_name='PROGRAMKIT_CACHE_CONTRACT_SENTINEL'
    sentinel_parent=os.environ.get(sentinel_name)
    ambient={name:str(evidence/'ambient-unrelated'/name) for name in cache_names}
    for value in ambient.values():
        destination=Path(value); destination.mkdir(parents=True)
        (destination/'cache-contract-marker.txt').write_text('untouched ambient marker',encoding='utf-8')
    script=evidence/'cache_child.py'
    script.write_text('import json,os,sys\nfrom pathlib import Path\n'
        +'names='+repr(cache_names)+'\n'
        +'paths={name:os.environ.get(name) for name in names}\n'
        +'seen={name:(Path(value)/"cache-contract-marker.txt").exists() if value else False for name,value in paths.items()}\n'
        +'if sys.argv[1]=="write":\n'
        +' for value in set(paths.values()):\n'
        +'  destination=Path(value); destination.mkdir(parents=True,exist_ok=True)\n'
        +'  (destination/"cache-contract-marker.txt").write_text("owned child acquisition marker",encoding="utf-8")\n'
        +'print(json.dumps({"paths":paths,"markersBefore":seen,"sentinel":os.environ.get('+repr(sentinel_name)+')}))\n'
        +'sys.exit(int(sys.argv[2]))\n',encoding='utf-8')
    consumers=[evidence/'cache-consumer-a',evidence/'cache-consumer-b']
    try:
        os.environ.update(ambient); os.environ[sentinel_name]='unchanged unrelated environment'
        for index,consumer in enumerate(consumers):
            consumer.mkdir()
            require_cold_cache(consumer)
            directory=evidence/('cache-cold-'+str(index))
            command([sys.executable,str(script),'write','0'],consumer,directory,timeout=30)
            observed=json.loads((directory/'stdout.log').read_text())
            expected={'PROGRAMKIT_NPM_CACHE':str(consumer/'artifacts/cache/npm'),
                'NPM_CONFIG_CACHE':str(consumer/'artifacts/cache/npm'),
                'PLAYWRIGHT_BROWSERS_PATH':str(consumer/'artifacts/cache/profile/local/ms-playwright')}
            assert observed['paths']==expected and not any(observed['markersBefore'].values())
            assert observed['sentinel']=='unchanged unrelated environment'
            assert json.loads((directory/'result.json').read_text())['consumerAcquisitionCaches']==expected
            assert {name:os.environ.get(name) for name in cache_names}==ambient
            rejected('cold-consumer-'+str(index)+'-refuses-acquired-owned-cache',lambda:require_cold_cache(consumer))
        prepared=evidence/'cache-prepared'
        command([sys.executable,str(script),'write','0'],consumers[0],prepared,timeout=30)
        observed=json.loads((prepared/'stdout.log').read_text())
        assert all(observed['markersBefore'].values())
        assert observed['paths']==json.loads((evidence/'cache-cold-0/stdout.log').read_text())['paths']
        failed=evidence/'cache-failed'
        try: command([sys.executable,str(script),'write','7'],consumers[0],failed,timeout=30)
        except ValueError: pass
        else: raise AssertionError('Actual cache child failure concealed')
        assert json.loads((failed/'result.json').read_text())['exitCode']==7
        assert {name:os.environ.get(name) for name in cache_names}==ambient
        inventory=evidence/'cache-repository-inventory'
        command([sys.executable,str(script),'observe','0'],ROOT,inventory,timeout=30)
        assert json.loads((inventory/'stdout.log').read_text())['paths']==ambient
        assert json.loads((inventory/'result.json').read_text())['consumerAcquisitionCaches']=={}
        for value in ambient.values():
            assert list(Path(value).iterdir())==[Path(value)/'cache-contract-marker.txt']
            assert (Path(value)/'cache-contract-marker.txt').read_text()=='untouched ambient marker'
        os.environ.pop('PROGRAMKIT_NPM_CACHE'); os.environ['NPM_CONFIG_CACHE']=''; os.environ.pop('PLAYWRIGHT_BROWSERS_PATH')
        sparse={name:os.environ.get(name) for name in cache_names}
        failed=evidence/'cache-sparse-parent-failed'
        try: command([sys.executable,str(script),'write','9'],consumers[0],failed,timeout=30)
        except ValueError: pass
        else: raise AssertionError('Actual sparse-parent child failure concealed')
        assert {name:os.environ.get(name) for name in cache_names}==sparse
        try:
            with consumer_cache_environment(consumers[0]): raise OSError('Expected supervisor exception')
        except OSError: pass
        assert {name:os.environ.get(name) for name in cache_names}==sparse
    finally:
        for name,value in {**parent,sentinel_name:sentinel_parent}.items():
            if value is None: os.environ.pop(name,None)
            else: os.environ[name]=value
    checks.extend(('distinct-cold-consumers-use-only-owned-npm-and-browser-cache-paths',
        'prepared-consumer-reuses-owned-acquisition-cache',
        'repository-inventory-preserves-ambient-cache-selection-without-writing-it',
        'actual-failed-cache-children-restore-present-empty-and-absent-parent-values'))
    authentication_contracts(evidence,checks,child,child_selected,secret)
    write(evidence/'qualification.json',{'status':'passed','checks':checks,'runtimeAcceptanceEstablished':False})
    print('Maintained qualification failure contracts passed: '+str(evidence))
    return 0


def authentication_contracts(evidence, checks, original_child, original_selected, secret):
    """Real report shapes and supervised failure; establishes no browser readiness."""
    import copy
    import xml.etree.ElementTree as ET
    source=ROOT/'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/web/tests/authentication.spec.ts'
    assert set(re.findall(r"^test\('([^']+)'",source.read_text(),re.MULTILINE))==set(AUTHENTICATION_CASES)
    directory=evidence/'authentication-report-fixtures'; directory.mkdir()
    path=directory/'authentication.xml'
    def report(rows):
        document=ET.Element('testsuites')
        suites={}
        for engine,title,outcome,message in rows:
            if engine not in suites: suites[engine]=ET.SubElement(document,'testsuite',name='authentication.spec.ts')
            node=ET.SubElement(suites[engine],'testcase',classname='authentication.spec.ts',name='['+engine+'] '+title)
            properties=ET.SubElement(node,'properties')
            ET.SubElement(properties,'property',name='skip' if outcome=='skipped' else secret,value=secret)
            if outcome: ET.SubElement(node,outcome,message=message).text=message
            ET.SubElement(node,'system-out').text=secret
        return ET.tostring(document,encoding='utf-8')
    titles=list(AUTHENTICATION_CASES)
    passing=[(engine,title,None,'') for engine in AUTHENTICATION_ENGINES for title in titles]
    path.write_bytes(report(passing))
    label=authentication_failure(directory,set())
    assert label=='authentication=no-failure authCases=21 authCompleteness=observed-complete authFailed=none authSkipped=none authenticationFailure=unknown'
    assert secret not in label
    checks.append('exact-maintained-authentication-titles-and-engines-project-only-bounded-ids')
    failed=list(passing); failed[0]=('chromium',titles[0],'failure','Error: browserType.launch: '+secret)
    failed[8]=('firefox',titles[1],'error','browserType.launch: '+secret)
    failed[-1]=('webkit',titles[-1],'skipped',secret)
    path.write_bytes(report(failed)); launch_report=path.read_bytes()
    label=authentication_failure(directory,set())
    assert label=='authentication=failed authCases=21 authCompleteness=observed-complete authFailed=chromium:anonymous-session,firefox:governed-headers authSkipped=webkit:permission-boundary authenticationFailure=browser-launch'
    assert secret not in label
    checks.append('current-junit-failed-skipped-cases-and-secret-annotations-never-export-prose')
    for marker,category in (('Test timeout of 30000ms exceeded. '+secret,'test-timeout'),
                            ('Error: expect(received).toEqual(expected) '+secret,'assertion'),
                            ('prefix browserType.launch: '+secret,'unknown')):
        path.write_bytes(report([('chromium',titles[0],'failure',marker)]))
        label=authentication_failure(directory,set())
        assert label.endswith('authenticationFailure='+category) and secret not in label
    checks.append('exact-maintained-timeout-and-assertion-prefixes-project-only-fixed-diagnostic-categories')
    path.write_bytes(report([('chromium',titles[0],'failure',secret)]))
    label=authentication_failure(directory,set())
    assert 'authentication=failed authCases=1 authCompleteness=partial' in label
    assert label.endswith('authenticationFailure=unknown') and secret not in label
    path.write_bytes(report([('chromium',titles[0],None,'')]))
    assert 'authentication=no-failure authCases=1 authCompleteness=partial' in authentication_failure(directory,set())
    path.write_bytes(report([('chromium',titles[0],'skipped',secret)]))
    assert authentication_failure(directory,set()).startswith('authentication=skipped authCases=1 authCompleteness=partial')
    path.write_bytes(report([]))
    assert authentication_failure(directory,set())=='authentication=empty authCases=0 authCompleteness=empty authFailed=none authSkipped=none authenticationFailure=unknown'
    path.unlink(); assert authentication_failure(directory,set())=='authentication=absent'
    checks.append('partial-skipped-empty-and-missing-reports-do-not-infer-browser-launch-or-acceptance')
    for data in (report(passing+[passing[0]]),report([('other',titles[0],'failure',secret)]),
                 report([('chromium',secret,'failure',secret)]),b'<testsuites><testcase/></testsuites>',
                 b'<testsuites><testsuite name="other"/></testsuites>',b'not-xml '+secret.encode(),
                 launch_report.replace(b'classname="authentication.spec.ts"',b'classname="injected"',1),
                 launch_report.replace(b'<failure ',b'<skipped/><failure ',1),
                 b'<testsuites><testsuite name="authentication.spec.ts"><testcase classname="authentication.spec.ts" name="[chromium] '+titles[0].encode()+b'"><failure><testcase/></failure></testcase></testsuite></testsuites>'):
        path.write_bytes(data); assert authentication_failure(directory,set())=='authentication=unknown'
    checks.append('unknown-duplicate-contradictory-or-malformed-authentication-cases-fail-closed')
    for data in (b'<!DOCTYPE testsuites [<!ENTITY secret "'+secret.encode()+b'">]>'+launch_report,
                 (b'<!DOCTYPE testsuites [<!ENTITY secret "'+secret.encode()+b'">]>'+launch_report).decode().encode('utf-16'),
                 launch_report.decode().encode('utf-16-le'),b'\xef\xbb\xbf'+launch_report,
                 b'<?xml version="1.0" encoding="iso-8859-1"?>'+launch_report,b'\xff'+launch_report,
                 b' '*1048577):
        path.write_bytes(data); assert authentication_failure(directory,set())=='authentication=unknown'
    path.write_bytes(launch_report)
    assert authentication_failure(directory,{path})=='authentication=unknown'
    checks.append('stale-oversized-dtd-entity-and-non-utf8-authentication-report-refused')
    from unittest.mock import patch
    original_resolve=Path.resolve
    def escaped(item,*args,**keywords):
        return evidence/'outside-authentication.xml' if item==path else original_resolve(item,*args,**keywords)
    with patch.object(Path,'resolve',escaped): assert authentication_failure(directory,set())=='authentication=unknown'
    class OversizedStream:
        def __enter__(self): return self
        def __exit__(self,*_): pass
        def read(self,size): assert size==1048577; return b' '*size
    with patch.object(Path,'open',return_value=OversizedStream()):
        assert authentication_failure(directory,set())=='authentication=unknown'
    checks.append('authentication-report-confinement-and-bounded-read-enforced-before-projection')
    # Actual maintained setup and supervisor execute only no-op Python stages and
    # this controlled native reporter child, which fails before native report admission.
    child=evidence/'authentication-failed-readiness-child'; child.mkdir()
    for filename in ('foundation_process.py','fail_setup.py'): shutil.copy2(original_child/filename,child/filename)
    script=child/'fail_authentication.py'
    script.write_text('import sys\nfrom pathlib import Path\n'
        +'directory=Path(sys.argv[1]); (directory/"authentication.xml").write_bytes('+repr(launch_report)+')\n'
        +'print('+repr(secret)+',file=sys.stderr); sys.exit(13)\n',encoding='utf-8')
    selected=copy.deepcopy(original_selected)
    for row in selected['setup']['steps']: row['command']=[sys.executable,'-c','pass']
    selected['tests']['commands'][0]['command']=[sys.executable,str(script),'{runDirectory}']
    write(child/'selected.json',selected)
    try: command([sys.executable,str(child/'fail_setup.py')],child,evidence/'authentication-failed-readiness-command',timeout=30,readiness=True)
    except ValueError as error:
        label=str(error)
        assert 'stage=check stepExit=13 code=PKF003 checkpoint=integration-absent childExit=unknown authentication=failed authCases=21' in label
        assert 'authFailed=chromium:anonymous-session,firefox:governed-headers' in label
        assert 'authenticationFailure=browser-launch outerExit=2;' in label and secret not in label
    else: raise AssertionError('Actual failed authentication reporter child concealed')
    checks.append('actual-maintained-readiness-child-classifies-authentication-without-secret-or-stream-export')
    # An actual command overwrites an existing report, but its pre-command
    # snapshot must prevent that stale path from establishing new classification.
    stale=evidence/'authentication-stale-readiness-child'; stale.mkdir()
    run_directory=stale/'artifacts/tests/runs/foundation-fixture'; run_directory.mkdir(parents=True)
    (run_directory/'authentication.xml').write_bytes(launch_report)
    receipt={'schemaVersion':1,'kind':'foundation-readiness','status':'failed','steps':[{'stage':'host-activation','exitCode':13}],
             'failure':'PKF003 fixture'}
    script=stale/'overwrite_authentication.py'
    script.write_text('import json,sys\nfrom pathlib import Path\n'
        +'directory=Path("artifacts/tests/runs/foundation-fixture")\n'
        +'(directory/"result.json").write_text('+repr(json.dumps(receipt))+',encoding="utf-8")\n'
        +'(directory/"authentication.xml").write_bytes('+repr(launch_report)+')\n'
        +'sys.exit(2)\n',encoding='utf-8')
    try: command([sys.executable,str(script)],stale,evidence/'authentication-stale-readiness-command',timeout=30,readiness=True)
    except ValueError as error:
        assert 'authentication=unknown outerExit=2;' in str(error) and secret not in str(error)
    else: raise AssertionError('Stale native reporter child failure concealed')
    checks.append('actual-precommand-snapshot-rejects-overwritten-stale-authentication-report')


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def browser_cache_inventory(*, environment=None, platform=None, home=None):
    """Observe cache directories portably; this never establishes browser readiness."""
    environment = os.environ if environment is None else environment
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    declared = environment.get('PLAYWRIGHT_BROWSERS_PATH')
    if declared == '0':
        cache = None  # Package-local caches depend on the installed Playwright module.
        source = 'package-local; no shared cache selected'
    elif declared:
        cache = Path(declared).expanduser().resolve()
        source = 'PLAYWRIGHT_BROWSERS_PATH'
    elif platform == 'win32':
        cache = Path(environment.get('LOCALAPPDATA') or home/'AppData/Local')/'ms-playwright'
        source = 'Windows ambient cache'
    elif platform == 'darwin':
        cache = home/'Library/Caches/ms-playwright'
        source = 'macOS ambient cache'
    else:
        cache = Path(environment.get('XDG_CACHE_HOME') or home/'.cache')/'ms-playwright'
        source = 'Linux ambient cache'
    exists = cache is not None and cache.is_dir()
    directories = sorted(path.name for path in cache.iterdir() if path.is_dir()) if exists else []
    return {'platform':platform, 'cacheSource':source, 'cachePath':str(cache) if cache is not None else None,
            'directoryExists':exists, 'observedDirectories':directories,
            'browserReadinessEstablished':False,
            'scope':'Pre-setup directory inventory only; installed executables and usability require actual browser checks.'}


def readiness_failure(root, previous, previous_children=frozenset()):
    """Project only finite failure labels from this invocation's owned metadata.

    Never forward streams, exception prose, command arguments or receipt paths.
    Ambiguous, stale, malformed and escaping receipts establish no classification.
    """
    unknown='stage=unknown stepExit=unknown code=unknown'
    try:
        directory=(root/'artifacts/tests/runs').resolve()
        if not directory.is_relative_to(root.resolve()): return unknown
        added=set(directory.glob('foundation-*/result.json'))-previous
        if len(added)!=1: return unknown
        path=added.pop()
        def read_owned(path):
            if path.resolve()!=path.absolute() or not path.resolve().is_relative_to(directory) or path.stat().st_size>131072:
                raise ValueError('Invalid diagnostic metadata')
            value=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value,dict): raise ValueError('Invalid diagnostic metadata')
            return value
        value=read_owned(path)
        if (type(value.get('schemaVersion')) is not int or value.get('schemaVersion')!=1 or value.get('kind')!='foundation-readiness'
                or value.get('status') not in ('failed','interrupted','running')): return unknown
        steps=value.get('steps')
        if not isinstance(steps,list) or not all(isinstance(row,dict) for row in steps): return unknown
        stage='unknown'; step_exit='unknown'
        if steps:
            final=steps[-1]
            raw_stage=final.get('stage')
            if raw_stage in ('restore','build','services'): stage=raw_stage
            elif raw_stage in ('host-activation','bff-cookie','keycloak','postgresql'): stage='check'
            observed=final
            process=path.parent/('command-'+format(len(steps),'02d'))/'process.json'
            if 'exitCode' not in observed and process.is_file(): observed=read_owned(process)
            exit_code=observed.get('exitCode')
            if type(exit_code) is int and -2147483648<=exit_code<=4294967295:
                step_exit=str(exit_code)
        failure=value.get('failure')
        matched=re.match(r'^(PKF00[1-5])(?:[ \t]|$)',failure) if isinstance(failure,str) else None
        code=matched.group(1) if matched else 'unknown'
        classification='stage='+stage+' stepExit='+step_exit+' code='+code
        if stage=='check':
            classification+=' '+integration_failure(path.parent,read_owned,previous_children)
            classification+=' '+authentication_failure(path.parent,previous_children)
        return classification
    except (OSError,ValueError,TypeError,RecursionError):
        return unknown


def integration_failure(directory, read_owned, previous):
    """Known checkpoints and bounded numeric exits only; never export child content."""
    unknown='checkpoint=unknown childExit=unknown'
    try:
        artifact=directory/'integration.json'
        checkpoint='integration-absent'
        if artifact.exists() or artifact.is_symlink():
            if artifact in previous: return unknown
            value=read_owned(artifact)
            if (type(value.get('schemaVersion')) is not int or value.get('schemaVersion')!=1
                    or value.get('status') not in ('running','failed','passed')): return unknown
            cases=value.get('cases')
            known={'Foundation.public_issuer_private_backchannel','Foundation.actual_selected_feature_activation',
                   'Foundation.actual_bound_effective_settings','Foundation.maintained_bff_cookie',
                   'Foundation.provider_connectivity_restart'}
            if (not isinstance(cases,dict) or not set(cases)<=known
                    or not all(type(item) is bool for item in cases.values())): return unknown
            passed={case for case,item in cases.items() if item}
            host={'Foundation.actual_selected_feature_activation','Foundation.actual_bound_effective_settings'}
            if passed & host and not host<=passed: return unknown
            identity='Foundation.public_issuer_private_backchannel' in passed
            activated=host<=passed
            authenticated='Foundation.maintained_bff_cookie' in passed
            provider='Foundation.provider_connectivity_restart' in passed
            if (activated and not identity) or (authenticated and not activated) or (provider and not authenticated): return unknown
            checkpoint='before-issuer-check'
            if identity: checkpoint='identity-ready'
            transport=value.get('runtimeTransport',[])
            if not isinstance(transport,list) or len(transport)>2: return unknown
            if transport:
                if not all(isinstance(row,dict) and row.get('phase') in ('initial','migration')
                           and isinstance(row.get('before'),dict) and row['before'].get('byteIdentityVerified') is True
                           for row in transport): return unknown
                if identity: checkpoint='host-copied'
            timings=value.get('timings',{})
            if not isinstance(timings,dict): return unknown
            if 'hostReadinessSeconds' in timings:
                duration=timings['hostReadinessSeconds']
                if type(duration) not in (int,float) or not 0<=duration<=1800 or not identity: return unknown
                checkpoint='host-ready'
            if activated: checkpoint='activated'
            if authenticated: checkpoint='authenticated'
            if provider: checkpoint='provider-restarted'
            if value['status']=='passed':
                if not authenticated or value.get('cleanupComplete') is not True: return unknown
                checkpoint='integration-completed'
        paths=list(directory.glob('process-*/process.json'))
        if len(paths)>128 or sum(path.stat().st_size for path in paths)>1048576: return unknown
        exits=set()
        for path in paths:
            if path in previous or not re.fullmatch(r'process-[0-9a-f]{32}',path.parent.name): return unknown
            value=read_owned(path)
            observed=value.get('exitCode')
            if value.get('status') not in ('completed','failed','interrupted'): return unknown
            if observed is None: continue
            if type(observed) is not int or not -2147483648<=observed<=4294967295: return unknown
            if observed: exits.add(observed)
        child_exit=str(next(iter(exits))) if len(exits)==1 else 'unknown'
        return 'checkpoint='+checkpoint+' childExit='+child_exit
    except (OSError,ValueError,TypeError,RecursionError):
        return unknown


AUTHENTICATION_CASES = {
    'anonymous browser has no BFF session':'anonymous-session',
    'WEB-V3 same-origin BFF response has the governed browser headers':'governed-headers',
    'real browser form logout clears local state and completes provider navigation':'session-logout',
    'missing or invalid browser antiforgery logout does not clear the session':'antiforgery-denial',
    'cross-site top-level logout form fails before session mutation':'cross-site-denial',
    'provider navigation failure cannot restore local access or displace the signed-out page':'provider-navigation-failure',
    'configured permission endpoint distinguishes authorized and unauthorized users':'permission-boundary',
}
AUTHENTICATION_ENGINES = ('chromium','firefox','webkit')


def authentication_failure(directory, previous):
    """Only exact maintained case IDs and finite outcomes from this invocation's JUnit."""
    import xml.etree.ElementTree as ET
    unknown='authentication=unknown'
    try:
        directory=Path(directory)
        owned=(ROOT/'artifacts/tests/reusable-foundations').resolve()
        if directory.resolve()!=directory.absolute() or not directory.resolve().is_relative_to(owned): return unknown
        path=directory/'authentication.xml'
        if path in previous: return unknown
        if path.is_symlink() or path.resolve()!=path.absolute() or not path.resolve().is_relative_to(directory): return unknown
        if not path.exists(): return 'authentication=absent'
        if not path.is_file() or path.stat().st_size>1048576: return unknown
        with path.open('rb') as stream: raw=stream.read(1048577)
        if len(raw)>1048576 or raw.startswith(b'\xef\xbb\xbf'): return unknown
        text=raw.decode('utf-8',errors='strict')
        if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): return unknown
        encoding=re.match(r"^\s*<\?xml\b[^?]*encoding\s*=\s*['\"]([^'\"]+)['\"]",text,re.IGNORECASE)
        if encoding and encoding.group(1).lower()!='utf-8': return unknown
        document=ET.fromstring(text)
        if document.tag!='testsuites' or any(suite.tag!='testsuite' or suite.get('name')!='authentication.spec.ts' for suite in document): return unknown
        cases=[]
        for suite in document:
            for node in suite:
                if node.tag=='testcase': cases.append(node)
                elif node.tag in ('system-out','system-err'):
                    if list(node): return unknown
                elif node.tag=='properties':
                    if any(item.tag!='property' or list(item) for item in node): return unknown
                else: return unknown
        if len(cases)>21 or len(cases)!=sum(1 for node in document.iter() if node.tag=='testcase'): return unknown
        identities=set(); failed=[]; skipped=[]; categories=[]
        for node in cases:
            if node.get('classname')!='authentication.spec.ts': return unknown
            match=re.fullmatch(r'\[(chromium|firefox|webkit)\] (.+)',node.get('name',''))
            if not match or match.group(2) not in AUTHENTICATION_CASES: return unknown
            identity=match.group(1)+':'+AUTHENTICATION_CASES[match.group(2)]
            if identity in identities: return unknown
            identities.add(identity)
            for child in node:
                if child.tag=='properties':
                    if any(item.tag!='property' or list(item) for item in child): return unknown
                elif child.tag not in ('failure','error','skipped','system-out','system-err') or list(child): return unknown
            outcomes=[child for child in node if child.tag in ('failure','error','skipped')]
            if len(outcomes)>1: return unknown
            if outcomes and outcomes[0].tag=='skipped': skipped.append(identity)
            elif outcomes:
                failed.append(identity)
                failure=outcomes[0]
                recognized=set()
                for value in (failure.get('message',''),failure.text or ''):
                    value=value.lstrip()
                    if value.startswith(('Error: browserType.launch:','browserType.launch:')): recognized.add('browser-launch')
                    elif re.match(r'^(?:Error: )?Test timeout of [1-9][0-9]{0,8}ms exceeded(?:[. \n]|$)',value): recognized.add('test-timeout')
                    elif value.startswith(('Error: expect(','expect(')): recognized.add('assertion')
                categories.append(next(iter(recognized)) if len(recognized)==1 else 'unknown')
        engines={identity.split(':',1)[0] for identity in identities}
        complete=bool(cases) and len(cases)==len(engines)*len(AUTHENTICATION_CASES)
        status='failed' if failed else 'skipped' if skipped else 'no-failure' if cases else 'empty'
        completeness='observed-complete' if complete else 'partial' if cases else 'empty'
        category=categories[0] if categories and len(set(categories))==1 else 'unknown'
        return ('authentication='+status+' authCases='+str(len(cases))+' authCompleteness='+completeness
            +' authFailed='+(','.join(sorted(failed)) or 'none')+' authSkipped='+(','.join(sorted(skipped)) or 'none')
            +' authenticationFailure='+category)
    except (OSError,ValueError,TypeError,RecursionError,ET.ParseError):
        return unknown


@contextmanager
def consumer_cache_environment(root):
    """Scope acquisition only for owned disposable consumers; restore the caller exactly."""
    root=root.resolve()
    owned=(ROOT/'artifacts/tests/reusable-foundations').resolve()
    if root==owned or not root.is_relative_to(owned):
        yield {}
        return
    cache=root/'artifacts/cache'
    paths={'PROGRAMKIT_NPM_CACHE':cache/'npm', 'NPM_CONFIG_CACHE':cache/'npm',
           'PLAYWRIGHT_BROWSERS_PATH':cache/'profile/local/ms-playwright'}
    if any(not path.resolve().is_relative_to(root) for path in paths.values()):
        raise ValueError('Owned acquisition cache escaped the disposable consumer')
    selected={name:str(path) for name,path in paths.items()}
    previous={name:os.environ.get(name) for name in selected}
    try:
        os.environ.update(selected)
        yield selected
    finally:
        for name,value in previous.items():
            if value is None: os.environ.pop(name,None)
            else: os.environ[name]=value


def require_cold_cache(root):
    cache=root/'artifacts/cache'
    if not cache.resolve().is_relative_to(root.resolve()):
        raise ValueError('Owned acquisition cache escaped the disposable consumer')
    for path in cache.rglob('*'):
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Owned acquisition cache escaped the disposable consumer')
        if path.is_file() and path.name!='.gitignore':
            raise ValueError('Cold qualification requires a new consumer and acquisition cache')


def command(args, root, evidence, *, timeout=1800, readiness=False):
    previous=set((root.resolve()/'artifacts/tests/runs').glob('foundation-*/result.json')) if readiness else set()
    previous_children=(set((root.resolve()/'artifacts/tests/runs').glob('foundation-*/integration.json'))
        | set((root.resolve()/'artifacts/tests/runs').glob('foundation-*/process-*/process.json'))
        | set((root.resolve()/'artifacts/tests/runs').glob('foundation-*/authentication.xml'))) if readiness else set()
    evidence.mkdir(parents=True)
    with consumer_cache_environment(root) as caches:
        with (evidence/'stdout.log').open('wb') as out,(evidence/'stderr.log').open('wb') as err:
            code=run(args,root,out,err,timeout)
    write(evidence/'result.json',{'exitCode':code,'command':args,'consumerAcquisitionCaches':caches})
    if code:
        classification=('; readiness '+readiness_failure(root,previous,previous_children)+' outerExit='+str(code)) if readiness else ''
        raise ValueError('Qualification command failed'+classification+'; inspect '+str(evidence))


def candidate(root, feed):
    import dependency_profile
    # Build candidate only from the explicit base already selected by Program Kit.
    resolver=dependency_profile.resolver()
    effective=resolver.effective_dependency_context(root)
    rows={}
    for package in ('Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication.BffCookie'):
        archives=list(feed.glob(package+'.*.nupkg'))
        if len(archives)!=1: raise ValueError('Explicit candidate feed must contain one exact package: '+package)
        archive=archives[0]
        destination=root/'eng/development-packages'/archive.name
        destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(archive,destination)
        import zipfile
        with zipfile.ZipFile(archive) as packed:
            metadata=json.loads(packed.read('orbyss-foundation/settings.json'))
        rows[package]={'path':destination.relative_to(root).as_posix(),'version':metadata['packageVersion'],
                       'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    profile=root/'eng/foundation-development-candidate.json'
    write(profile,{'id':'reusable-foundations-development','baseProfile':effective['profile'],'status':'development-candidate','packages':rows})
    return {'profile':profile.relative_to(root).as_posix(),'sha256':hashlib.sha256(profile.read_bytes()).hexdigest()}


def sync(root, evidence, *, check=False, expected=0):
    args=[sys.executable,str(SCRIPTS/'dotnet_sync.py'),'--target',str(root),'--profile-selected',
          '--foundation-host-accepted','--building-block-sources-approved','--web-profile','bff-cookie','--json']
    if check: args.append('--check')
    if expected==0: command(args,ROOT,evidence)
    else:
        evidence.mkdir(parents=True)
        with (evidence/'stdout.log').open('wb') as out,(evidence/'stderr.log').open('wb') as err:
            code=run(args,ROOT,out,err,300)
        if code!=expected: raise ValueError('Expected reviewed sync status '+str(expected)+'; inspect '+str(evidence))
        write(evidence/'result.json',{'exitCode':code,'expected':expected})


def scaffold(root, shape, feed, evidence):
    postgres=shape!='base'
    variant='foundation-bff-keycloak'+('-postgresql' if postgres else '')
    config=composition.read(ROOT/'extensions/program-kit-dotnet/templates/dotnet/compositions'/(variant+'.json'))
    config['runner']='xunit-mtp' if shape=='sport' else 'executable'
    config['runtime']['directory']='runtime/nested/persoonlijk' if shape=='sport' else '.'
    if shape=='sport':
        config['identity']['publicOrigin']='http://localhost:18080'
        config['identity']['realm']='sport-qualification'
        extra={'path':'src/Nieuws/Feed.Api/Feed.Api.csproj','packageId':'Feed.Api','featureIdentity':'Feed.Api','role':'implementation'}
        config['projects'].append(extra); config['runtime']['rootPackages'].append(extra['packageId'])
    root.mkdir(parents=True)
    write(root/composition.INPUT,config)
    sync(root,evidence/'initial-sync')
    if feed:
        config['developmentCandidate']=candidate(root,feed)
        write(root/composition.INPUT,config)
        sync(root,evidence/'candidate-sync')
    # Product sources and native tests are application-owned. All fixture/service
    # lifecycle, authentication, reporting and settings capture come from tooling.
    if postgres:
        first=root/config['projects'][0]['path']
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/OwnedResourceFeature.cs',first.parent/'ApiFeature.cs')
        core=root/'src/Product.Core'; core.mkdir(parents=True)
        (core/'Product.Core.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><IsPackable>true</IsPackable><PackageId>Product.Core</PackageId></PropertyGroup></Project>',encoding='utf-8')
        for name in ('IOwnedResources.cs','ResourceOwner.cs','CreateResourceOutcome.cs'):
            shutil.copy2(ROOT/'tests/fixtures/reusable-foundations'/name,core/name)
        project=first.read_text(encoding='utf-8').replace('</Project>',
            '<ItemGroup><ProjectReference Include="../Product.Core/Product.Core.csproj" /></ItemGroup></Project>')
        first.write_text(project,encoding='utf-8')
        provider=root/config['projects'][1]['path']
        provider.write_text(provider.read_text().replace('</Project>','<ItemGroup><ProjectReference Include="../Product.Core/Product.Core.csproj" /></ItemGroup></Project>'),encoding='utf-8')
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/OwnedResources.cs',provider.parent/'OwnedResources.cs')
        feature=provider.parent/'ProviderFeature.cs'
        feature.write_text(feature.read_text().replace('services.AddFoundationPostgreSql',
            'services.AddSingleton<Product.Core.IOwnedResources, OwnedResources>();\n        services.AddFoundationPostgreSql'),encoding='utf-8')
        dependencies=first.read_text().replace('Orbyss.Foundation.Authentication;Orbyss.Foundation.WebDefaults','Orbyss.Foundation.Authentication;Orbyss.Foundation.WebDefaults;Application.PostgreSql')
        first.write_text(dependencies,encoding='utf-8')
        product=root/'tests/foundation-product/qualification.mjs'; product.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/qualification.mjs',product)
        shutil.copy2(ROOT/'tests/fixtures/reusable-foundations/schema.sql',product.parent/'schema.sql')
    projects=[p['path'] for p in config['projects']]
    if postgres: projects.append('src/Product.Core/Product.Core.csproj')
    if shape=='sport':
        tests=root/'tests/Product/Product.Tests.csproj'; tests.parent.mkdir(parents=True)
        tests.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><IsTestProject>true</IsTestProject><IsPackable>false</IsPackable><UseMicrosoftTestingPlatformRunner>true</UseMicrosoftTestingPlatformRunner></PropertyGroup><ItemGroup><PackageReference Include="xunit.v3.mtp-v2" /></ItemGroup></Project>',encoding='utf-8')
        (tests.parent/'ProductBoundaryTests.cs').write_text('''namespace Qualification.Product;
/// <summary>Native product security assertion against the activated selected host.</summary>
public sealed class ProductBoundaryTests
{
    /// <summary>The browser resource route challenges anonymously without disclosing the resource.</summary>
    [Xunit.Fact]
    public async System.Threading.Tasks.Task AnonymousResourceReadChallengesWithoutDisclosure()
    {
        using var handler = new System.Net.Http.HttpClientHandler { AllowAutoRedirect = false };
        using var client = new System.Net.Http.HttpClient(handler)
        {
            BaseAddress = new System.Uri(System.Environment.GetEnvironmentVariable("PROGRAMKIT_BASE_URL")
                ?? throw new System.InvalidOperationException("Actual host URL required"))
        };
        const string resourcePath = "/resources/fc78aeb7-529f-4906-a9a5-8db4ff8a6ead";
        using var response = await client.GetAsync(resourcePath, Xunit.TestContext.Current.CancellationToken);
        // The selected BFF contract returns401 for /api; this browser route challenges locally.
        Xunit.Assert.Equal(System.Net.HttpStatusCode.Found, response.StatusCode);
        var location = response.Headers.Location;
        Xunit.Assert.NotNull(location);
        var target = new System.Uri(client.BaseAddress, location);
        Xunit.Assert.Equal(client.BaseAddress.GetLeftPart(System.UriPartial.Authority), target.GetLeftPart(System.UriPartial.Authority));
        Xunit.Assert.Equal("/bff/login", target.AbsolutePath);
        Xunit.Assert.Equal("?ReturnUrl=" + System.Uri.EscapeDataString(resourcePath), target.Query);
        Xunit.Assert.Empty(await response.Content.ReadAsStringAsync(Xunit.TestContext.Current.CancellationToken));
    }
}
''',encoding='utf-8')
        packages=root/'Directory.Packages.props'
        test_pins=json.loads((root/'eng/foundation-test-support/packages.json').read_text())
        packages.write_text(packages.read_text().replace('</Project>','<ItemGroup><PackageVersion Include="xunit.v3.mtp-v2" Version="'+test_pins['xunit.v3.mtp-v2']+'" /></ItemGroup></Project>'),encoding='utf-8')
        projects.append(tests.relative_to(root).as_posix())
    (root/'Application.slnx').write_text('<Solution>\n'+''.join('<Project Path="'+p+'" />\n' for p in projects)+'</Solution>\n',encoding='utf-8')
    (root/'VERSION').write_text('0.0.1-development\n' if feed else '0.0.1\n',encoding='utf-8')
    architecture=composition.read(root/'eng/architecture.json')
    if postgres:
        for item in architecture['runtimeComposition']['projects']:
            if item['path'] in (config['projects'][0]['path'],config['projects'][1]['path']):
                item['projectReferences']=['src/Product.Core/Product.Core.csproj']
        architecture['runtimeComposition']['projects'].append({'path':'src/Product.Core/Product.Core.csproj','role':'core','projectReferences':[],
            'responsibilities':[{'name':'Product.Core.IOwnedResources','kind':'contract','effects':[]}]})
        architecture['runtimeComposition']['bindings']=[{'capabilityProject':'src/Product.Core/Product.Core.csproj',
            'implementationProject':config['projects'][1]['path'],'capability':'Product.Core.IOwnedResources',
            'implementation':'Application.PostgreSql.OwnedResources','registration':'Application.PostgreSql.ProviderFeature.ConfigureServices'}]
    if shape=='sport':
        architecture['runtimeComposition']['projects'].append({'path':'tests/Product/Product.Tests.csproj','role':'test','projectReferences':[],
            'responsibilities':[{'name':'ProductBoundaryTests','kind':'test','effects':['Actual HTTP owner-read authentication prerequisite']}]})
    write(root/'eng/architecture.json',architecture)
    # Preserve synthetic accepted history/customization and locks through reviewed sync.
    (root/'docs/architecture/adoption-history.md').write_text('Disposable accepted architecture history. No live consumer adoption.\n',encoding='utf-8')
    if postgres:
        shells=composition.read(root/'shells.json')
        shells['CShells']['Shells']['default'].setdefault('Configuration',{}).setdefault('Foundation',{}).setdefault('Web',{})['RemoteAuthenticationTimeoutSeconds']=11
        write(root/'shells.json',shells)
    sync(root,evidence/'rerun-sync')
    return config


def qualify(root, shape, phase, evidence, generation):
    os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='0' if shape=='base' else '1'
    if phase=='cold': require_cold_cache(root)
    started=time.monotonic()
    command([sys.executable,'eng/foundation_setup.py','--repository','.','--execute'],root,evidence/'readiness',readiness=True)
    runs=sorted((root/'artifacts/tests/runs').glob('foundation-*/result.json'),key=lambda p:p.stat().st_mtime)
    native=json.loads(runs[-1].read_text())
    if native['status']!='ready': raise ValueError('Generated composition failed actual readiness')
    integration=json.loads((runs[-1].parent/'integration.json').read_text())
    if shape!='base' and integration.get('productAcceptance') is not True:
        raise ValueError('First actual authenticated owner operation not established')
    timings={'generationSeconds':round(generation,3), **{row['stage']+'Seconds':row['elapsedSeconds'] for row in native['steps']},
             **{key:value for key,value in json.loads((runs[-1].parent/'restore-timings.json').read_text()).items() if key!='elapsedSeconds'},
             **integration['timings'], 'readinessTotalSeconds':round(time.monotonic()-started,3),
             'generationToFirstOperationUpperBoundSeconds':round(generation+time.monotonic()-started,3) if shape!='base' else None}
    if shape!='base':
        timings['generationToFirstWorkingProductOperationSeconds']=round(generation + sum(row['elapsedSeconds'] for row in native['steps'] if row['stage'] in ('restore','build','services')) + integration['timings']['integrationToFirstProductOperationSeconds'],3)
    result={'shape':shape,'phase':phase,'status':'passed','coldDefinition':'Fresh isolated NuGet/npm caches and browser downloads; preinstalled SDK/Docker images disclosed separately' if phase=='cold' else 'Same consumer acquired dependency/browser caches',
            'newConsumerAuthoredGenericHarnessLines':0,'remainingGenericSetupTasks':0,'timings':timings,
            'readinessArtifact':str(runs[-1].relative_to(ROOT)), 'productionBundle':composition.resolve(root)['runtimeStage']}
    write(evidence/'result.json',result)
    return result


def migrate(root, config, evidence):
    """Real product data stays alive across the maintained reviewed adoption path."""
    owned_orphans={}
    if config['runner']=='xunit-mtp':
        independent=root/config['projects'][-1]['path']
        text=independent.read_text()
        if '<Description>Consumer-owned Sport news feed</Description>' not in text:
            independent.write_text(text.replace('<IsPackable>true</IsPackable>',
                '<IsPackable>true</IsPackable>\n    <Description>Consumer-owned Sport news feed</Description>'),encoding='utf-8')
        source=independent.parent/'ApiFeature.cs'
        if 'ConsumerFeedName' not in source.read_text():
            source.write_text(source.read_text().replace('public sealed class ApiFeature : IWebShellFeature\n{',
                'public sealed class ApiFeature : IWebShellFeature\n{\n    /// <summary>Consumer-owned independent feed identity.</summary>\n    public const string ConsumerFeedName = "Sport news";'),encoding='utf-8')
        owned_orphans={path.relative_to(root).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in (independent,source)}
        write(evidence/'consumer-owned-orphan-inputs.before.json',{'beforeFeatureRemoval':True,'files':owned_orphans})
    directory=root/'artifacts/tests/runs'/('migration-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    command([sys.executable,'eng/foundation_qualification.py','--repository','.','--run-directory',directory.relative_to(root).as_posix(),
             '--migration','--product','--sync-script',str(SCRIPTS/'dotnet_sync.py')],root,evidence/'actual-product-migration')
    result=json.loads((directory/'integration.json').read_text())
    if result['status']!='passed' or not result.get('migration',{}).get('retainedProductAfterUpgrade'):
        raise ValueError('Actual consumer product data did not survive reviewed migration')
    if owned_orphans:
        assert all((root/path).is_file() and hashlib.sha256((root/path).read_bytes()).hexdigest()==expected for path,expected in owned_orphans.items())
        removed=config['projects'][-1]['packageId']
        assert result['migration']['removedIndependentFeature']==config['projects'][-1]['featureIdentity']
        built=list((root/'artifacts/packages').rglob(removed+'.*.nupkg'))
        assert built and not list((root/composition.resolve(root)['runtimeStage']/'packages').glob(removed+'.*.nupkg'))
        result['migration']['preservedConsumerOwnedOrphanInputs']=owned_orphans
        result['migration']['orphanBuiltPackage']={'path':str(max(built,key=lambda p:p.stat().st_mtime).relative_to(root)),
            'excludedFromSelectedRuntime':True}
    write(evidence/'result.json',result['migration'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shape',choices=('base','notes','sport','all'),default='all')
    parser.add_argument('--candidate-feed',type=Path)
    parser.add_argument('--prepared',action='store_true',help='Measure a second acquired-cache run in the same consumer')
    parser.add_argument('--contract-tests',action='store_true',help='Bounded failure-contract checks; starts no external service or package restore')
    parser.add_argument('--engines',default='chromium,webkit',help='Actual maintained browser engines; CI includes Firefox')
    parser.add_argument('--functional-consumer',type=Path,help='Reuse a preserved disposable bundle/cache for functional repairs; establishes no cold timing or readiness receipt')
    parser.add_argument('--migration-consumer',type=Path,help='Resume actual retained-data migration on a preserved disposable consumer; establishes no new timing claim')
    parser.add_argument('--default-readiness',action='store_true',help='With a preserved consumer, run actual default foundation setup without application proving')
    parser.add_argument('--product-failure',nargs='?',const='initial',choices=('initial','retained'),help='With an owned functional consumer, retain real platform success beside an intentionally failed application assertion')
    args=parser.parse_args()
    if args.contract_tests: return contract_tests()
    engines=args.engines.split(',')
    if not engines or not set(engines)<={'chromium','webkit','firefox'}: parser.error('Unsupported browser engine selection')
    os.environ['PROGRAMKIT_BROWSER_ENGINES']=args.engines
    if args.migration_consumer:
        root=args.migration_consumer.resolve()
        if not root.is_relative_to(ROOT/'artifacts/tests/reusable-foundations') or not (root/composition.INPUT).is_file():
            parser.error('Migration must target an owned disposable qualification consumer')
        artifact=ROOT/'artifacts/tests/reusable-foundations'/('migration-repair-'+uuid.uuid4().hex[:16]); artifact.mkdir()
        config=composition.read(root/composition.INPUT)
        if config['runner']=='xunit-mtp' and not any(row['packageId']=='Feed.Api' for row in config['projects']):
            config['projects'].append({'path':'src/Nieuws/Feed.Api/Feed.Api.csproj','packageId':'Feed.Api','featureIdentity':'Feed.Api','role':'implementation'})
            config['runtime']['rootPackages'].append('Feed.Api')
            write(root/composition.INPUT,config)
        sync(root,artifact/'synchronize-reviewed-ownership-repair')
        directory=root/'artifacts/tests/runs'/('migration-preparation-'+uuid.uuid4().hex); directory.mkdir()
        command([sys.executable,'eng/foundation_qualification.py','--repository','.',
            '--run-directory',directory.relative_to(root).as_posix(),'--stage','build'],root,artifact/'prepare-selected-initial-bundle')
        migrate(root,config,artifact/'migration')
        write(artifact/'qualification.json',{'status':'migration-passed','consumer':str(root.relative_to(ROOT)),
              'newColdTimingClaim':False,'actualMigration':str((artifact/'migration/result.json').relative_to(ROOT))})
        print('Actual repaired consumer migration: '+str(artifact))
        return 0
    if args.functional_consumer:
        root=args.functional_consumer.resolve()
        if not root.is_relative_to(ROOT/'artifacts/tests/reusable-foundations') or not (root/composition.INPUT).is_file():
            parser.error('Functional consumer must be a preserved owned disposable qualification consumer')
        artifact=ROOT/'artifacts/tests/reusable-foundations'/('functional-'+uuid.uuid4().hex[:16])
        artifact.mkdir(parents=True)
        sync(root,artifact/'synchronize-repaired-test-support')
        if args.default_readiness:
            if args.product_failure: parser.error('Default readiness and application failure proving are separate modes')
            product=root/'tests/foundation-product/qualification.mjs'
            if not product.is_file(): parser.error('Default independence proof requires an existing owned application adapter')
            before=set((root/'artifacts/tests/runs').glob('*/result.json'))
            os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='0'
            observer=artifact/'command-observer'; observer.mkdir()
            audit=artifact/'command-audit'; audit.mkdir()
            (observer/'sitecustomize.py').write_text('''import json, os, uuid
from pathlib import Path
import foundation_fixture
_original = foundation_fixture.captured
def _observed(command, cwd, directory, **keywords):
    safe = [str(token) for token in command]
    for value in keywords.get('secret_values', ()):
        if value:
            safe = [token.replace(value, '[REDACTED]') for token in safe]
    destination = Path(os.environ['PROGRAMKIT_COMMAND_AUDIT']) / (uuid.uuid4().hex + '.json')
    destination.write_text(json.dumps({'command':safe, 'cwd':str(cwd)}, indent=2), encoding='utf-8')
    return _original(command, cwd, directory, **keywords)
foundation_fixture.captured = _observed
''',encoding='utf-8')
            previous={name:os.environ.get(name) for name in ('PYTHONPATH','PROGRAMKIT_COMMAND_AUDIT')}
            os.environ['PYTHONPATH']=os.pathsep.join((str(observer),str(root/'eng'),previous['PYTHONPATH'] or ''))
            os.environ['PROGRAMKIT_COMMAND_AUDIT']=str(audit)
            try:
                command([sys.executable,'eng/foundation_setup.py','--repository','.', '--execute'],root,artifact/'default-setup',readiness=True)
            finally:
                for name,value in previous.items():
                    if value is None: os.environ.pop(name,None)
                    else: os.environ[name]=value
            added=set((root/'artifacts/tests/runs').glob('*/result.json'))-before
            receipts=[path for path in added if json.loads(path.read_text()).get('kind')=='foundation-readiness']
            if len(receipts)!=1: raise ValueError('Default readiness must retain one actual maintained setup receipt')
            receipt=receipts[0]; observed=json.loads(receipt.read_text()); directory=receipt.parent
            integration=json.loads((directory/'integration.json').read_text())
            product_result=json.loads((directory/'product-acceptance.json').read_text())
            assert observed['status']=='ready' and integration['status']=='passed' and all(integration['cases'].values())
            assert product_result['phase']['status']=='not-requested' and integration['productAcceptance'] is False
            assert 'productPhases' not in integration and 'product' not in integration and 'nativeTests' not in integration
            assert 'firstProductOperationWithSessionsSeconds' not in integration['timings']
            assert 'nativeApplicationTestsSeconds' not in integration['timings']
            assert not any(json.loads(path.read_text()).get('scope')=='Focused' for path in added)
            assert not any((directory/name).exists() for name in ('product-operation.json','product-retained-after-restart.json'))
            recorded=[json.loads(path.read_text()) for path in audit.glob('*.json')]
            assert len(recorded)>20 and any(row['command'][:2]==['docker','run'] for row in recorded)
            assert any(any('playwright' in token for token in row['command']) and 'test' in row['command'] for row in recorded)
            schema_requested=any(any('product-schema.sql' in token or 'foundation-product/schema.sql' in token for token in row['command']) for row in recorded)
            driver_executed=any(any('product_driver.mjs' in token for token in row['command']) for row in recorded)
            native_executed=any(any('repository_verification.py' in token for token in row['command']) and 'Focused' in row['command'] for row in recorded)
            assert not schema_requested and not driver_executed and not native_executed
            write(artifact/'default-readiness.json',{'status':'passed','productAdapterPresent':True,
                'productOptIn':False,'actualPlatformCases':integration['cases'],'productAcceptance':False,
                'productPhase':product_result['phase'],'nativeApplicationRunCreated':native_executed,
                'productDriverOutputCreated':driver_executed,'applicationSchemaDeploymentRequested':schema_requested,
                'actualObservedCommandCount':len(recorded),
                'commandAuditScope':'Test-only Python startup observer of maintained foundation_fixture.captured across owned descendants. Redacted argv and owned cwd only; delegates original command, arguments and supervision unchanged.',
                'commandAudit':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in audit.glob('*.json')},
                'actualReadiness':str(receipt.relative_to(ROOT)),
                'adapterSha256':hashlib.sha256((root/'eng/foundation_qualification.py').read_bytes()).hexdigest()})
            print('Actual default setup independence: '+str(artifact))
            return 0
        directory=root/'artifacts/tests/runs'/('functional-'+uuid.uuid4().hex); directory.mkdir(parents=True)
        product=root/'tests/foundation-product/qualification.mjs'
        original=product.read_bytes() if product.is_file() else None
        os.environ['PROGRAMKIT_QUALIFY_PRODUCT']='1' if original is not None else '0'
        if args.product_failure:
            if original is None: parser.error('Real failed-product qualification requires the owned product fixture')
            if args.product_failure=='initial':
                product.write_text('export async function qualify() { throw new Error("Expected owned application assertion failure"); }\n',encoding='utf-8')
            else:
                needle='  if (process.env.PROGRAMKIT_RETAINED_RESOURCE_ID) {'
                text=original.decode('utf-8')
                if needle not in text: parser.error('Retained-product failure requires the exact owned fixture seam')
                product.write_text(text.replace(needle,needle+'\n    throw new Error("Expected owned retained-product assertion failure");'),encoding='utf-8')
        try:
            command([sys.executable,'eng/foundation_qualification.py','--repository','.',
                     '--run-directory',directory.relative_to(root).as_posix(),'--check','host-activation'],root,artifact/'integration')
            if args.product_failure:
                result=json.loads((directory/'integration.json').read_text())
                if result['status']!='passed' or result['productAcceptance'] is not False or result['productPhase'].get('failure')!='application-proving-failed' or not all(result['cases'].values()):
                    raise ValueError('Actual failed product erased platform proof or concealed application failure')
                write(artifact/'expected-product-failure.json',{'platformStatus':result['status'],'actualPlatformCases':result['cases'],
                     'productAcceptance':False,'productFailure':result['productPhase'],'actualIntegration':str(directory.relative_to(ROOT))})
        finally:
            if args.product_failure and original is not None: product.write_bytes(original)
        write(artifact/'qualification.json',{'status':'functional-checks-passed','actualIntegration':str(directory.relative_to(ROOT)),
              'coldTimingEstablished':False,'foundationReadinessReceiptEstablished':False})
        print('Functional prepared integration: '+str(artifact))
        return 0
    if args.default_readiness: parser.error('Default readiness requires a preserved owned consumer')
    artifact=ROOT/'artifacts/tests/reusable-foundations'/uuid.uuid4().hex[:16]
    artifact.mkdir(parents=True)
    write(artifact/'status.json',{'status':'running'})
    results=[]
    try:
        # Inventory is measured before setup, not retroactively classified.
        for name,args_inventory in [('images',['docker','image','ls','--digests']),('sdk',['dotnet','--list-sdks'])]:
            command(args_inventory,ROOT,artifact/('preexisting-'+name),timeout=30)
        write(artifact/'preexisting-browser-cache/inventory.json',browser_cache_inventory())
        for shape in (('base','notes','sport') if args.shape=='all' else (args.shape,)):
            root=artifact/shape/'consumer'
            start=time.monotonic()
            config=scaffold(root,shape,args.candidate_feed,artifact/shape/'generation')
            generation=time.monotonic()-start
            results.append(qualify(root,shape,'cold',artifact/shape/'cold',generation))
            if args.prepared: results.append(qualify(root,shape,'prepared',artifact/shape/'prepared',0))
            if shape!='base': migrate(root,config,artifact/shape/'migration')
        write(artifact/'qualification.json',{'status':'passed','results':results,
             'publicationQualified':False,'adoption':'Explicit disposable-only development qualification; live Notes/Sport unchanged'})
        write(artifact/'status.json',{'status':'passed'})
    except BaseException as error:
        write(artifact/'status.json',{'status':'failed','failure':str(error),'completed':results})
        print('Retained failed qualification: '+str(artifact),file=sys.stderr)
        raise
    print('Reusable foundations qualification: '+str(artifact))
    return 0


if __name__=='__main__': raise SystemExit(main())
