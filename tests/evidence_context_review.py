"""Installed F2/F3 walkthrough in the same retained, actually executed F5 consumer."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from owned_fixture import filesystem_path

ROOT = Path(__file__).resolve().parents[1]


def scenario(work, review, witness):
    def write(path, value):
        path.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(value,bytes):path.write_bytes(value)
        else:path.write_text(value if isinstance(value,str) else json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    records=[]
    def run(name,arguments,expected=0):
        result=subprocess.run(list(map(str,arguments)),cwd=work,capture_output=True,text=True,encoding='utf-8',timeout=90)
        write(review/'context-output'/(name+'.stdout.txt'),result.stdout)
        write(review/'context-output'/(name+'.stderr.txt'),result.stderr)
        records.append({'name':name,'arguments':list(map(str,arguments)),'expectedExit':expected,'actualExit':result.returncode,
                        'stdoutSha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'stderrSha256':hashlib.sha256(result.stderr.encode()).hexdigest()})
        write(review/'context-results.json',{'status':'running','commands':records})
        if result.returncode!=expected:raise AssertionError('F5 installed context step failed: '+name)
        return result.stdout
    for component in ('program-kit-governance','program-kit-dotnet','program-kit-building-blocks'):
        shutil.copytree(filesystem_path(ROOT/'extensions'/component),filesystem_path(work/'.specify/extensions'/component),ignore=shutil.ignore_patterns('__pycache__'))
    extensions=work/'.specify/extensions'; governance=extensions/'program-kit-governance/scripts'
    native=extensions/'program-kit-dotnet/templates/dotnet/files/eng/repository_verification.py'
    phase=governance/'phase_obligations.py'; patterns=governance/'coding_patterns.py'
    feature=work/'specs/001-evidence'
    write(feature/'spec.md','# Fictional evidence desk\nA signed-in fictional reviewer confirms title/date/text, retains one submission identity and reconciles an unknown result.\n- **Specification roadmap entry**: RM-F5\n')
    plan='# Fictional accepted fixture design\nUse Evidence Core, scoped runtime, thin API and owned PostgreSQL. Browser FileReader selection generations consume the owning input contract; native UI and session controls remain selected.\nProjects: '+', '.join('src/'+role+'/Evidence.'+role+'.csproj' for role in ('Core','Runtime','Api','PostgreSql'))+'.\nFrontend: web/package.json.\nOnly fictional data; the final example home is the maintained evidence-submission subtree. Retain the temporary copy/navigation/tests until human review. No real authentication, paid/provider operation, general distributed guarantee or human visual acceptance.\n'
    write(feature/'plan.md',plan)
    tasks='''# Fictional F5 task inputs
- [ ] T001 [US1] Implement .NET HTTP evidence submission through src/Api/Evidence.Api.csproj, src/Runtime/Evidence.Runtime.csproj, src/Core/Evidence.Core.csproj and PostgreSQL src/PostgreSql/Evidence.PostgreSql.csproj; use the TypeScript browser in web/package.json and FileReader selection generations.
- [ ] T002 [US1] Verify real providers, confirmation, unknown recovery and rendered browser controls.

## Operation dependency map
| Operation | Depends on operations |
|-----------|-----------------------|
| submit | none |

## Task dependency map
| Task | Operation | Depends on tasks | Requires | Provides |
|------|-----------|------------------|----------|----------|
| T001 | submit | none | none | none |
| T002 | submit | T001 | none | none |
'''
    write(feature/'tasks.md',tasks)
    write(work/'.program-kit/specification-intake/RM-F5/brief.json',{'architectureScope':['evidence'],'decisions':[]})
    write(work/'docs/architecture/bootstrap-decisions.json',{'selected_profiles':['dotnet','typescript-web']})
    schema=work/'contracts/evidence-model.json';shutil.copyfile(work/'accepted-model.json',schema) if schema.parent.exists() else write(schema,(work/'accepted-model.json').read_bytes())
    write(work/'docs/architecture/architecture-map.json',{'elements':[{'id':'evidence','type':'bounded-context','technology':'.NET','decision_refs':['evidence-runtime']}],
      'decisions':[{'id':'evidence-runtime','status':'Accepted'}],
      'sources':[{'id':'evidence-contract','path':'contracts/evidence-model.json','sha256':hashlib.sha256(schema.read_bytes()).hexdigest()}],
      'strategic_model':{'bounded_contexts':[{'element':'evidence','status':'accepted'}],
                         'contracts':[{'id':'evidence-submission','owner':'evidence','kind':'command','status':'accepted','evidence':['evidence-contract']}]}})
    namespace='ProgramKit.Examples.Evidence.'
    bindings=[{'capabilityProject':'src/Core/Evidence.Core.csproj','implementationProject':'src/'+role+'/Evidence.'+role+'.csproj',
               'capability':namespace+capability,'implementation':namespace+implementation,'registration':namespace+feature+'.ConfigureServices'}
              for role,capability,implementation,feature in [('Runtime','IEvidenceSubmissions','EvidenceSubmissions','EvidenceRuntimeFeature'),
                    ('PostgreSql','IEvidenceJournal','PostgreSqlEvidenceJournal','EvidenceProviderFeature')]]
    projects=[]
    for role,kind in [('Core','contract'),('Runtime','runtime'),('Api','http'),('PostgreSql','persistence')]:
        path='src/'+role+'/Evidence.'+role+'.csproj'
        references=[] if role=='Core' else ['src/Core/Evidence.Core.csproj']
        implementation=next((row for row in bindings if row['implementationProject']==path),None)
        responsibility={'name':implementation['implementation'] if implementation else 'Evidence'+role,'kind':kind,'effects':[] if role=='Core' else [kind]}
        if implementation:responsibility['provides']=[implementation['capability']]
        packages=[row.get('Include') for row in ET.parse(work/path).iter('PackageReference')]
        projects.append({'path':path,'role':{'Core':'core','Runtime':'implementation','Api':'implementation','PostgreSql':'provider'}[role],
                         'packageReferences':packages,'projectReferences':references,'responsibilities':[responsibility]})
    probe='tests/Probe/Evidence.Probe.csproj'
    projects.append({'path':probe,'role':'test','projectReferences':[row['path'] for row in projects],
                     'packageReferences':[row.get('Include') for row in ET.parse(work/probe).iter('PackageReference')],
                     'responsibilities':[{'name':'Actual shell/API/provider fixture','kind':'test','effects':['http','persistence'],
                                          'testSeams':['shell-lifecycle','api-feature']} ]})
    pins={row.get('Include'):row.get('Version') for row in ET.parse(work/probe).iter('PackageReference')}
    write(work/'Directory.Packages.props','<Project><ItemGroup>'+''.join('<PackageVersion Include="'+name+'" Version="'+version+'" />' for name,version in pins.items())+'</ItemGroup></Project>')
    write(work/'eng/architecture.json',{'runtimeComposition':{'projects':projects,'bindings':bindings}})
    run('compiled-actual-owner-graph',[sys.executable,native.with_name('repository_architecture.py'),
        '--repository',work,'--manifest','eng/architecture.json','--output','proof/architecture.xml'])
    shutil.copyfile(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/eng/Invoke-RepositoryVerification.ps1',work/'eng/Invoke-RepositoryVerification.ps1')
    write(work/'web/package.json',{'name':'fictional-evidence-browser','version':'1.0.0','private':True,'type':'module','devDependencies':{'typescript':'7.0.2'}})
    write(work/'.gitignore','.specify/\nartifacts/\n**/bin/\n**/obj/\n')
    git=['git','-c','safe.directory='+str(work),'-c','core.excludesFile=']
    for name,args in [('init',['init','-q']),('add',['add','.']),('baseline',['-c','user.name=Fictional F5 Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Fictional F5 accepted source inputs'])]:
        run(name,git+args)
    baseline=run('baseline-identity',git+['rev-parse','HEAD']).strip()
    sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
    import task_draft
    task_draft.checkpoint(feature,{'baseline':baseline,'outcome':'Fictional F5 source and actual test witnesses','next':'Prepare the scoped coding route'})
    query=work/'specs/002-query';write(query/'spec.md','# Read-only evidence query\n.NET HTTP PostgreSQL read-only observation.\n- **Specification roadmap entry**: RM-F5\n')
    write(query/'plan.md','Read-only query in src/Api/Evidence.Api.csproj and src/PostgreSql/Evidence.PostgreSql.csproj. No browser or independent domain-event reactions are required.\n')
    write(query/'tasks.md',tasks.replace('submit','observe').replace(tasks.splitlines()[1],'- [ ] T001 [US1] Read-only .NET HTTP query in src/Api/Evidence.Api.csproj and src/PostgreSql/Evidence.PostgreSql.csproj.').replace('Verify real providers, confirmation, unknown recovery and rendered browser controls.','Verify owner isolation.'))
    task_draft.checkpoint(query,{'baseline':baseline,'outcome':'Fictional independent query','next':'Prepare its independent scope'})
    write(work/'proof/actual-witness.json',witness)
    shutil.copyfile(work/'native-result.json',work/'proof/native-result.json')
    shutil.copyfile(work/'browser-result.json',work/'proof/browser-result.json')
    write(work/'tests/observation_check.py','''import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
native=json.loads((root/'proof/native-result.json').read_text())
required={'independent-accepted-table-authority','independent-accepted-column-authority','business-preparation-independent-of-http','actual-provider-json-and-business-acceptance','real-http-mapping-and-nondefault-options','actual-provider-scope-disposal'}
assert required <= set(native['checks'])
browser=json.loads((root/'proof/browser-result.json').read_text())
assert {'chromium','webkit'} <= {r['engine'] for r in browser['outcomes']}
for row in browser['outcomes']:
 assert row['acceptanceRequests']==1 and row['immutableConfirmation'] and row['retainedReconciliation'] and row['sessionBoundary']
assert browser['nativeDocumentGeneratedClient'] and browser['invalidWireTypeRejected']
witness=json.loads((root/'proof/actual-witness.json').read_text())
process=next(row['process'] for row in witness['commands'] if row['name']=='actual-application')
assert process['exitCode']==0 and process['cleanupComplete'] and process['logsDrained']
print('Independent F5 observation assertions passed; witnessed native application and actual browsers, not a new application execution or authenticated receipt.')
''')
    inputs=[path.relative_to(work).as_posix() for path in (work/'src').rglob('*') if path.is_file() and not {'bin','obj'} & set(path.parts)]
    inputs+=['global.json','accepted-model.json','eng/architecture.json','proof/architecture.xml','proof/native-result.json','proof/browser-result.json','proof/actual-witness.json']
    for name in ('model-drift','owner-bypass'):
        candidates=list((review/'snapshots'/name).rglob('*.cs'))
        if candidates:write(work/'examples/invalid'/(name+'.cs.txt'),candidates[0].read_bytes())
        else:write(work/'examples/invalid'/(name+'.cs.txt'),'Fictional rejected control: wrong model or omitted owner predicate. See the separately compiled native controls.\n')
    write(work/'eng/verification.json',{'schemaVersion':1,'testGroups':[],'toolkitChecks':[{'id':'evidence-observation','script':'tests/observation_check.py','arguments':[],
          'inputs':inputs,'timeoutSeconds':20}]})
    write(work/'docs/architecture/evidence-source-review.md','# Fictional authored source review\nCore owns valid immutable content, runtime owns admission, API owns wire mapping, provider owns atomic effects and owner predicates. Actual native and browser witnesses are retained. Fictional identity/headers are test-only; production native authentication/antiforgery remains mandatory. Events and physical fencing are separately scoped. This review is attributable source, not authenticated human product acceptance.\n')
    invariants=['principle.compilation-boundaries','principle.ui-state-recovery','principle.query-shape']
    reference=lambda path:{'root':'repository','path':path}
    unit={'id':'local-evidence-submission','ruleIds':invariants,'when':{'all':['api','persistence','web']},'requiredContext':['request','model-owner','contract-owner','effective-projects','verification-owner'],'route':'manual-edit',
          'pattern':{'schemaVersion':1,'semanticId':'evidence-submission','version':'1.0.0','owner':'fictional F5 source reviewer','status':'active','invariantRuleIds':invariants,
           'compatibility':{'profiles':['dotnet'],'frameworks':['net10.0'],'packages':{'Orbyss.Foundation.Json.AspNetCore':'0.3.6','Npgsql.EntityFrameworkCore.PostgreSQL':'10.0.3'}},
           'alternatives':[],'replaces':[],'inputs':[reference(path) for path in inputs],
           'examples':{'positive':[reference('src/Runtime/EvidenceSubmissions.cs')],'negative':[reference('examples/invalid/model-drift.cs.txt'),reference('examples/invalid/owner-bypass.cs.txt')]},
           'checks':[{'kind':'toolkit','id':'evidence-observation'}],'review':reference('docs/architecture/evidence-source-review.md'),'evidence':[],
           'limits':'Fictional source-specific application and immutable native/browser witnesses. Named toolkit check verifies observations, not a fresh native run. F3 exact package compatibility is .NET only; arbitrary language/toolchain changes and authenticated history are not inferred.',
           'provenance':'Actual F5 retained disposable consumer; no stopped consumer, private promotion or agent consultation claim.'}}
    write(work/'docs/architecture/coding-patterns.json',{'schemaVersion':1,'sources':[],'rules':{},'codingUnits':[unit]})
    write(feature/'plan.md',plan+'\n<!-- program-kit:pattern-choices -->\n'+json.dumps({'evidence-submission':{'id':unit['id'],'version':'1.0.0','reason':'Fictional evidence context with current actually executed source and scoped observation proof.'}})+'\n<!-- /program-kit:pattern-choices -->\n')
    def prepare(name,where=feature,operation='submit',expected=0):
        return json.loads(run(name,[sys.executable,phase,'prepare','--repository',work,'--feature-dir',where,'--operation',operation,'--format','json'],expected))
    rejected=prepare('01-unqualified-explicit-pattern',expected=2)
    assert any(b['code']=='PKP005' for b in rejected['coding']['blockers'])
    run('02-actual-observation-check',[sys.executable,native,'--repository',work,'--scope','Focused','--check','evidence-observation'])
    run('03-bind-current-pattern',[sys.executable,patterns,'bind-evidence','--repository',work,'--feature-dir',feature.relative_to(work).as_posix(),'--operation','submit','--id',unit['id']])
    selected=prepare('04-prepared-selected-family-route')
    assert unit['id'] in {row['id'] for row in selected['coding']['skills']}
    independent=prepare('05-unrelated-query',query,'observe')
    assert unit['id'] not in {row['id'] for row in independent['coding']['skills']}
    assert 'seed-independent-events' not in {row['id'] for row in independent['coding']['skills']}
    path=work/'src/Core/EvidencePacket.cs';original=path.read_bytes()
    write(review/'snapshots/context-before/src/Core/EvidencePacket.cs',original)
    try:
        path.write_bytes(original+b'\n// Fictional source-freshness mutation.\n')
        write(review/'snapshots/context-after/src/Core/EvidencePacket.cs',path.read_bytes())
        stale=prepare('06-stale-source-blocked',expected=2)
        assert any(b['code']=='PKP005' for b in stale['coding']['blockers'])
    finally:path.write_bytes(original)
    prepare('07-restored-source-context')
    write(review/'context-results.json',{'status':'passed','commands':records,'limits':'Installed-layout F2/F3 on the same actual source; fictional authoring/review and witness assertions do not authenticate their author or imply agent consultation.'})
