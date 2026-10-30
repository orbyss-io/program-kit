"""Real failed Playwright cases, both streams and attachments against the maintained private reporter."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
REPORTER = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/tools/program-kit/web/private-diagnostics.mjs'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser-root', type=Path, default=ROOT / 'artifacts/cache/f5-browser')
    args = parser.parse_args()
    work = ROOT / 'artifacts/t' / ('private-' + uuid.uuid4().hex[:8]); (work / 'cases').mkdir(parents=True)
    (work / 'package.json').write_text('{"private":true,"type":"module"}\n')
    secret = 'PRIVATE_SYNTHETIC_' + uuid.uuid4().hex
    imports = (args.browser_root / 'node_modules/playwright/test.mjs').as_uri()
    source = f'''import {{test,expect}} from {json.dumps(imports)};
import {{suppressPrivateErrors}} from {json.dumps(REPORTER.as_uri())};
test.afterEach(async({{}},info)=>{{suppressPrivateErrors(info);}});
test.describe('setup',()=>{{
  test.beforeEach(()=>{{throw new Error({json.dumps(secret)});}});
  test('setup rejection',()=>{{throw new Error('body must not execute');}});
}});
test({json.dumps(secret)},async({{page}},info)=>{{
  await page.setContent('<main>'+{json.dumps(secret)}+'</main>');
  console.log({json.dumps(secret)}); console.error({json.dumps(secret)});
  await info.attach('private dynamic title',{{body:Buffer.from({json.dumps(secret)}),contentType:'text/plain'}});
  expect({json.dumps(secret)}).toBe('different');
}});
test('timeout',async()=>{{test.setTimeout(100);await new Promise(()=>{{}});}});
test('retry',async({{}},info)=>{{if(!info.retry) throw new Error({json.dumps(secret)});}});
'''
    (work / 'cases/private.spec.ts').write_text(source, encoding='utf-8')
    (work / 'cases-reporter-only').mkdir()
    hook='test.afterEach(async({{}},info)=>{{suppressPrivateErrors(info);}});'.format()
    (work / 'cases-reporter-only/private.spec.ts').write_text(source.replace(hook,''), encoding='utf-8')
    config = {'testDir':str(work / 'cases'),'testMatch':'private.spec.ts','outputDir':str(work / 'output'),
              'workers':1,'retries':1,'timeout':5000,'reporter':[[str(REPORTER),{'outputFile':'private-results.json'}]],
              'use':{'browserName':'chromium','trace':'off','screenshot':'off','video':'off'}}
    environment = dict(os.environ, PLAYWRIGHT_NO_COPY_PROMPT='1')
    invocations = []
    for name, setup in [('cases', False), ('reporter-only', False), ('unknown-global-setup', True)]:
        artifact = work / 'runs' / name
        selected = {**config, 'outputDir':str(artifact)}
        if name=='reporter-only': selected['testDir']=str(work/'cases-reporter-only')
        if setup:
            (work / 'setup.mjs').write_text('export default () => {throw new Error(' + json.dumps(secret) + ');};\n')
            selected['globalSetup'] = str(work / 'setup.mjs')
        path = work / (name + '.config.mjs'); path.write_text('export default ' + json.dumps(selected) + ';\n')
        command = ['node',str(args.browser_root / 'node_modules/playwright/cli.js'),'test','--config',str(path)]
        run = subprocess.run(command,cwd=work,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=90)
        (work / (name + '.stdout.txt')).write_text(run.stdout)
        (work / (name + '.stderr.txt')).write_text(run.stderr)
        if secret in run.stdout or secret in run.stderr: raise AssertionError('Private canary escaped a runner stream')
        if run.returncode != 1: raise AssertionError('Deliberately failed cases did not remain failed')
        report = json.loads(run.stdout.strip().splitlines()[-1])
        if setup:
            assert report['counts']['unknownLocations'] > 0 and report['counts']['errors'] > 0
        else:
            rows = report['outcomes']
            assert len(rows) == 8 and any(row['status']=='timedOut' for row in rows)
            assert any(row['retry']==1 and row['status']=='passed' for row in rows)
            assert any(row['stage']=='expect' for row in rows) and any(row['stage']=='hook' for row in rows)
            assert all(row['sourceId']=='source-1' and row['line']>0 for row in rows)
            assert report['counts']['stdoutEvents']>0 and report['counts']['stderrEvents']>0 and report['counts']['attachments']>0
            assert report['counts']['externalAttachments']==0
        for target in artifact.rglob('*'):
            if secret in target.name: raise AssertionError('Private dynamic title escaped in an artifact name')
            if target.is_file() and secret.encode() in target.read_bytes(): raise AssertionError('Private attachment or DOM escaped')
        invocations.append({'name':name,'command':command,'exitCode':run.returncode,'report':report,
                            'stdoutSha256':hashlib.sha256(run.stdout.encode()).hexdigest(),'stderrSha256':hashlib.sha256(run.stderr.encode()).hexdigest()})
    result = {'status':'passed','reporterSha256':hashlib.sha256(REPORTER.read_bytes()).hexdigest(),'runs':invocations,
              'limits':'Actual fictional failures only; source identity is local runner inventory, not authenticated authorship or inferred stacks.'}
    (work / 'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Private diagnostics actual failure proof: ' + str(work / 'result.json'))


if __name__ == '__main__': main()
