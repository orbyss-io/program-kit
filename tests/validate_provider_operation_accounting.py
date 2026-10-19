"""Offline account/authority mechanics; fictional admission seam is not provider or human acceptance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import contextlib
import io
import os
import shutil
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid
from owned_fixture import FixtureDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extensions/program-kit-governance/scripts'))
import provider_operation as operation
import provider_operation_authority as authority


class AccountingTests(unittest.TestCase):
    def setUp(self):
        temporary = FixtureDirectory(native=True)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.resource = '/subscriptions/fictional/resourceGroups/test/providers/Microsoft.CognitiveServices/accounts/fictional'
        self.account = operation.Account(self.root,self.resource)
        self.root=self.account.root
        self.identity = self.account.initialize(20_000,[])
        self.native = {'path':'fictional-proof.json','sha256':'e'*64,'kind':'compatibility'}
        self.admission = patch.object(operation,'native_admission',side_effect=lambda *_: dict(self.native))
        self.admission.start();self.addCleanup(self.admission.stop)
        fixture = self.root/'fixtures/document.pdf';fixture.parent.mkdir();fixture.write_bytes(b'%PDF-1.4\nsynthetic input\n%%EOF')
        adapter=self.root/'fixtures/adapter.json';adapter.write_text('{"scope":"fictional accounting mechanism only"}')
        self.value = {'schemaVersion':1,'operation':'ocr-read-only','adapter':operation.ADAPTER,
            'resourceIdentity':self.resource,'endpoint':'https://fictional-account.cognitiveservices.azure.com/',
            'fixture':{'path':'fixtures/document.pdf','sha256':operation.sha(fixture.read_bytes())},
            'adapterPreparation':{'path':'fixtures/adapter.json','sha256':operation.sha(adapter.read_bytes())},
            'account':{'identity':self.identity,'authorityPath':self.account.marker.relative_to(self.root).as_posix(),
                       'authoritySha256':operation.sha(self.account.marker.read_bytes())},
            'limits':{'submissions':1,'pages':1,'modelCalls':0,'sdkRetries':0,'fallback':False,
                      'maximumInputBytes':1024,'maximumResponseBytes':1024,'timeoutMilliseconds':5000,
                      'polls':2,'pollTimeoutMilliseconds':1000,'deletions':1,
                      'runReservationMicroUsd':10_000,'aggregateCeilingMicroUsd':20_000},
            'preparedAt':time.time(),'submitBefore':time.time()+60,'recoverBefore':time.time()+120,'credentialRef':'PROGRAMKIT_OCR_API_KEY'}

    def prepare(self):
        path=self.root/'fixtures/operation.json';path.write_bytes(operation.canonical(self.value))
        return operation.contract(self.root,'fixtures/operation.json')

    def authorize(self,prepared):
        path='authorizations/'+uuid.uuid4().hex+'.json'
        authority.issue_recording(self.root,path,prepared,self.native)
        return path

    def reserve(self):
        prepared=self.prepare()
        return self.account.reserve(prepared,'fictional-admission','fixtures/admission.py',self.authorize(prepared),execution='recording')

    def test_no_native_evidence_or_recording_manifest_can_become_provider_authority(self):
        prepared=self.prepare();path=self.authorize(prepared)
        with self.assertRaisesRegex(ValueError,'recording mode'):
            self.account.reserve(prepared,'fictional','fixtures/unused.py',path,execution='provider')
        (self.root/'native-only.json').write_text(json.dumps(self.native))
        with self.assertRaisesRegex(ValueError,'unsupported one-use'):
            self.account.reserve(prepared,'fictional','fixtures/unused.py','native-only.json',execution='recording')

    def test_one_use_authority_is_exclusively_consumed_across_actual_sqlite_connections(self):
        prepared=self.prepare();path=self.authorize(prepared)
        def contender(_):
            try:return self.account.reserve(prepared,'fictional','fixtures/unused.py',path,execution='recording')
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            result=list(pool.map(contender,range(8)))
        self.assertEqual(1,sum(item is not None for item in result))
        state=self.account.status(next(item for item in result if item is not None))
        self.assertEqual(10_000,state['aggregateReservedMicroUsd'])

    def test_unknown_after_dispatch_retains_full_reservation_and_cannot_submit_again(self):
        identity=self.reserve()
        self.account.dispatch_intent(identity)
        self.account.submission_outcome(identity,'unknown')
        with self.assertRaisesRegex(ValueError,'already dispatched or uncertain'):
            self.account.dispatch_intent(identity)
        with patch.object(self.account,'historical_admission'):
            with self.assertRaisesRegex(ValueError,'no owned handle'):
                self.account.recovery_intent(identity,'poll')
        self.assertEqual(10_000,self.account.status(identity)['aggregateReservedMicroUsd'])

    def test_original_handle_and_accounting_survive_new_session_and_cleanup_never_refunds(self):
        identity=self.reserve();self.account.dispatch_intent(identity)
        handle=str(uuid.uuid4());self.account.retain_handle(identity,handle)
        self.account.submission_outcome(identity,'unknown')
        reopened=operation.Account(self.root,self.resource)
        with patch.object(reopened,'historical_admission'):
            _,observed,poll=reopened.recovery_intent(identity,'poll')
            self.assertEqual(handle,observed)
            reopened.recovery_outcome(identity,poll,'succeeded','a'*64)
            _,_,deletion=reopened.recovery_intent(identity,'delete')
            with self.assertRaisesRegex(ValueError,'not observed result absence'):
                reopened.recovery_outcome(identity,deletion,'absent')
            reopened.recovery_outcome(identity,deletion,'unknown')
            _,_,absence=reopened.recovery_intent(identity,'poll')
            reopened.recovery_outcome(identity,absence,'absent')
            with self.assertRaisesRegex(ValueError,'already observed'):
                reopened.recovery_intent(identity,'poll')
        self.assertEqual(10_000,reopened.status(identity)['aggregateReservedMicroUsd'])

    def test_run_and_original_aggregate_caps_include_all_unknown_reservations(self):
        first=self.reserve();self.account.dispatch_intent(first);self.account.submission_outcome(first,'unknown')
        self.reserve()
        with self.assertRaisesRegex(ValueError,'aggregate ceiling'):
            self.reserve()
        self.assertEqual(20_000,self.account.status(first)['aggregateReservedMicroUsd'])

    def test_changed_fixture_or_operation_cannot_borrow_the_original_manifest(self):
        prepared=self.prepare();path=self.authorize(prepared)
        fixture=self.root/self.value['fixture']['path'];fixture.write_bytes(fixture.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'fixture changed'):
            self.account.reserve(prepared,'fictional','fixtures/unused.py',path,execution='recording')

    def test_unsupported_model_page_retry_fallback_and_unknown_fields_fail_before_reservation(self):
        for field,value in [('pages',2),('modelCalls',1),('sdkRetries',1),('fallback',True),('submissions',2),('pages',True)]:
            original=self.value['limits'][field];self.value['limits'][field]=value
            with self.assertRaises(ValueError):self.prepare()
            self.value['limits'][field]=original
        self.value['invented']='ignored-by-no-one'
        with self.assertRaisesRegex(ValueError,'unsupported operation contract'):self.prepare()

    def test_missing_or_deleted_or_tampered_reservations_are_not_fresh_budget(self):
        identity=self.reserve()
        with closing(sqlite3.connect(self.account.path)) as connection:
            connection.execute('DELETE FROM events')
            connection.commit()
        with self.assertRaisesRegex(ValueError,'were removed'):self.account.status(identity)
        with self.assertRaisesRegex(ValueError,'already exists'):self.account.initialize(20_000,[])

    def test_missing_grant_or_original_contract_fails_closed(self):
        identity=self.reserve()
        with closing(sqlite3.connect(self.account.path)) as connection:
            connection.execute('DELETE FROM grants')
            connection.commit()
        with self.assertRaisesRegex(ValueError,'missing or duplicate'):self.account.status(identity)

    def test_retained_account_marker_cannot_be_replaced_to_raise_budget(self):
        identity=self.reserve()
        marker=operation.load(self.account.marker);marker['ceiling']=1_000_000
        self.account.marker.write_bytes(operation.canonical(marker))
        with self.assertRaisesRegex(ValueError,'account authority changed'):self.account.status(identity)

    def test_copied_account_is_history_and_cannot_spend_from_a_second_store(self):
        identity=self.reserve()
        copied=operation.Account(self.root/'copy',self.resource)
        copied.directory.parent.mkdir(parents=True)
        shutil.copytree(self.account.directory,copied.directory)
        copied.marker.parent.mkdir(parents=True)
        shutil.copyfile(self.account.marker,copied.marker)
        with self.assertRaisesRegex(ValueError,'copied state is historical'):
            copied.status(identity)

    def test_losing_private_artifacts_does_not_initialize_a_fresh_budget(self):
        self.reserve()
        self.assertTrue(self.account.directory.resolve().is_relative_to(self.root))
        shutil.rmtree(self.account.directory)
        with self.assertRaisesRegex(ValueError,'already exists or is incomplete'):
            self.account.initialize(20_000,[])

    def test_expired_authority_and_reused_changed_confirmation_fail(self):
        prepared=self.prepare();path=self.authorize(prepared)
        manifest=operation.load(self.root/path);manifest['expiresAt']=time.time()-1;manifest['issuedAt']=time.time()-2
        (self.root/path).write_bytes(operation.canonical(manifest))
        with self.assertRaisesRegex(ValueError,'expired'):
            self.account.reserve(prepared,'fictional','fixtures/unused.py',path,execution='recording')

    def test_event_capacity_reserves_space_for_all_future_recovery_outcomes(self):
        with patch.object(operation,'MAX_EVENTS',10):
            identity=self.reserve()
            with self.assertRaisesRegex(ValueError,'finite accounting capacity'):
                self.reserve()
            self.account.dispatch_intent(identity)
            self.account.retain_handle(identity,str(uuid.uuid4()))
            self.account.submission_outcome(identity,'unknown')
            with patch.object(self.account,'historical_admission'):
                for action,status in [('poll','running'),('delete','unknown'),('poll','absent')]:
                    _,_,token=self.account.recovery_intent(identity,action)
                    self.account.recovery_outcome(identity,token,status)
            self.assertEqual(10,len(self.account.status(identity)['events']))

    def test_original_historical_reservations_are_charged_and_cannot_disappear(self):
        original=self.root/'prior-operation.json';original.write_text('{"synthetic":"unknown prior operation"}')
        resource=self.resource+'-history'
        account=operation.Account(self.root,resource)
        identity=account.initialize(20_000,[{'path':'prior-operation.json','sha256':operation.sha(original.read_bytes()),
                                          'reservationMicroUsd':15_000}])
        review=account.review()
        self.assertEqual(15_000,review['aggregateReservedMicroUsd'])
        self.assertEqual(20_000,review['originalCeilingMicroUsd'])
        original.unlink()
        with self.assertRaisesRegex(ValueError,'historical reservation is missing'):
            account.review()


class NativeAdmissionTests(unittest.TestCase):
    def test_actual_latest_native_receipt_and_recording_authority_in_separate_processes(self):
        from owned_fixture import filesystem_path, native_path
        import validate_bootstrap_lifecycle as fixture
        previous=Path.cwd()
        # Keep native package paths below Windows toolchain limits; retain this exact fixture.
        retained=ROOT/'artifacts/t'/('o-'+uuid.uuid4().hex[:8])
        retained.mkdir(parents=True)
        inputs=[Path(__file__),ROOT/'tests/provider-operation-cases.json',
                *sorted((ROOT/'extensions/program-kit-governance/scripts').glob('provider_operation*.py')),
                *sorted((ROOT/'extensions/program-kit-dotnet/references/examples/ocr-operation').glob('*'))]
        basis={file.relative_to(ROOT).as_posix():operation.sha(file.read_bytes()) for file in inputs if file.is_file()}
        metadata={'status':'running','scope':'Actual native admission and SDK with fictional one-use recording authority only',
                  'providerCalls':0,'modelCalls':0,'providerAcceptance':False,'cases':[],'processes':[]}
        with contextlib.nullcontext(filesystem_path(retained)) as name:
            root=Path(name)
            try:
                os.chdir(root)
                with contextlib.redirect_stdout(io.StringIO()):
                    fixture.setup(root)
                resource='/subscriptions/fictional/resourceGroups/test/providers/Microsoft.CognitiveServices/accounts/fictional'
                account=operation.Account(root,resource)
                identity=account.initialize(80_000,[])
                from provider_operation_prepare import prepare as prepare_adapter
                adapter_path=prepare_adapter(root)
                document=root/'fixtures/document.pdf';document.parent.mkdir();document.write_bytes(b'%PDF-1.4\nsynthetic\n%%EOF')
                value={'schemaVersion':1,'operation':'ocr-read-only','adapter':operation.ADAPTER,
                    'resourceIdentity':resource,'endpoint':'https://fictional-account.cognitiveservices.azure.com/',
                    'fixture':{'path':'fixtures/document.pdf','sha256':operation.sha(document.read_bytes())},
                    'adapterPreparation':{'path':adapter_path,'sha256':operation.sha((root/adapter_path).read_bytes())},
                    'account':{'identity':identity,'authorityPath':account.marker.relative_to(root).as_posix(),
                               'authoritySha256':operation.sha(account.marker.read_bytes())},
                    'limits':{'submissions':1,'pages':1,'modelCalls':0,'sdkRetries':0,'fallback':False,
                              'maximumInputBytes':1024,'maximumResponseBytes':1024,'timeoutMilliseconds':5000,
                              'polls':2,'pollTimeoutMilliseconds':1000,'deletions':1,
                              'runReservationMicroUsd':10_000,'aggregateCeilingMicroUsd':200_000},
                    'preparedAt':time.time(),'submitBefore':time.time()+180,'recoverBefore':time.time()+300,'credentialRef':'PROGRAMKIT_OCR_API_KEY'}
                configuration=root/'fixtures/operation.json';configuration.write_bytes(operation.canonical(value))
                recipe=root/'docs/architecture/compatibility/provider.py';recipe.parent.mkdir(parents=True)
                recipe.write_text('''import json,hashlib
from pathlib import Path
value=json.loads(Path('operation.json').read_text())
assert value['limits']['submissions']==1 and value['limits']['pages']==1 and value['limits']['modelCalls']==0
assert hashlib.sha256(Path('document.pdf').read_bytes()).hexdigest()==value['fixture']['sha256']
assert hashlib.sha256(Path('authority.json').read_bytes()).hexdigest()==value['account']['authoritySha256']
assert hashlib.sha256(Path('adapter.json').read_bytes()).hexdigest()==value['adapterPreparation']['sha256']
assert json.loads(Path('adapter.json').read_text())['status']=='passed'
Path('compatibility-results.xml').write_text('<testsuite><testcase classname="NativeAdmission" name="exact_fixture_account_and_operation"/></testsuite>')
''')
                contract={'schemaVersion':1,'result':'compatibility-results.xml','checks':[{
                    'id':'exact-operation','kind':'runtime-compatibility','testCases':['NativeAdmission.exact_fixture_account_and_operation']}],
                    'fixtures':{'operation.json':'fixtures/operation.json','document.pdf':'fixtures/document.pdf',
                                'adapter.json':adapter_path,
                                'authority.json':account.marker.relative_to(root).as_posix()}}
                recipe.with_suffix('.contract.json').write_text(json.dumps(contract))
                item=fixture.item()
                fixture.ledger(root,[item])
                proof=fixture.lifecycle.run_proof(root,'provider',recipe.relative_to(root).as_posix(),30)
                self.assertEqual(0,proof.pop('exit_code'))
                item.update(status='closed',evidence=[proof]);fixture.ledger(root,[item])
                prepared=operation.contract(root,'fixtures/operation.json')
                native=operation.native_admission(root,prepared,'provider',recipe.relative_to(root).as_posix())
                authority.issue_recording(root,'authorizations/one-use.json',prepared,native)
                def contender(_):
                    return subprocess.run([sys.executable,str(Path(__file__).resolve()),'--reserve-worker',str(root),resource],
                                          cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=60)
                with ThreadPoolExecutor(max_workers=8) as pool:
                    observed=list(pool.map(contender,range(8)))
                for index,result in enumerate(observed):
                    for stream in ('stdout','stderr'):
                        (root/f'contender-{index}.{stream}.log').write_text(getattr(result,stream),encoding='utf-8')
                    metadata['processes'].append({'command':result.args,'exitCode':result.returncode})
                self.assertEqual(1,sum(result.returncode==0 for result in observed),[r.stderr for r in observed])
                self.assertEqual(7,sum(result.returncode==77 for result in observed),[r.stderr for r in observed])
                selected=json.loads(next(result.stdout for result in observed if result.returncode==0))['attempt']
                account.dispatch_intent(selected)
                account.retain_handle(selected,str(uuid.uuid4()));account.submission_outcome(selected,'unknown')
                # Actual original native JUnit/receipt validation, with no patched
                # admission reader and no provider transport or human consent claim.
                _,_,poll=account.recovery_intent(selected,'poll')
                account.recovery_outcome(selected,poll,'absent')
                self.assertEqual(10_000,account.status(selected)['aggregateReservedMicroUsd'])
                metadata['cases'].append('eight-native-processes-one-use-admission-exactly-one-reservation')
                import provider_operation_execute as execute
                import provider_operation_prepare as preparation
                native_relative=recipe.relative_to(root).as_posix()
                attempts=[]
                def run(scenario):
                    authorization='authorizations/'+uuid.uuid4().hex+'.json'
                    authority.issue_recording(root,authorization,prepared,native)
                    result=execute.run(root,'fixtures/operation.json',authorization,'provider',native_relative,
                                       recording_outcome=scenario)
                    attempts.append(result['attempt'])
                    (root/('execution-'+scenario+'.json')).write_bytes(operation.canonical(result))
                    self.assertTrue(result['process']['streamsDrained'])
                    self.assertEqual(1 if scenario!='exit-before-transport' else 0,
                                     sum(event['event']=='recording-transport' for event in result['process']['events']))
                    return result
                # An ambient secret never enters recording workers or retained streams.
                sentinel='FICTIONAL-AMBIENT-KEY-'+uuid.uuid4().hex
                with patch.dict(os.environ,{'PROGRAMKIT_OCR_API_KEY':sentinel,'PROGRAMKIT_OCR_WORKER_KEY':sentinel}):
                    accepted=run('accepted')
                self.assertEqual('acknowledged',accepted['status'])
                attempt=accepted['attempt']
                success=execute.recover(root,resource,attempt,'poll',recording_outcome='succeeded')
                self.assertEqual('succeeded',success['status'])
                self.assertIsNotNone(success['privateResult'])
                deletion=execute.recover(root,resource,attempt,'delete',recording_outcome='delete-accepted')
                self.assertEqual('unknown',deletion['status'])
                absence=execute.recover(root,resource,attempt,'poll',recording_outcome='absent')
                self.assertEqual('absent',absence['status'])
                self.assertEqual(20_000,absence['account']['aggregateReservedMicroUsd'])
                metadata['cases'].append('actual-native-submit-result-delete-ack-separate-absence-no-refund')
                # Exact consumed native ticket cannot dispatch again or from a copied path.
                command=accepted['process']['command']
                replay=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=15,
                                      env=execute.runtime_environment('recording',None))
                self.assertNotIn('recording-transport',replay.stdout)
                metadata['processes'].append({'command':command,'exitCode':replay.returncode,'stdout':replay.stdout,'stderr':replay.stderr})
                ticket=Path(filesystem_path(Path(command[-2])));copied=ticket.with_name(str(uuid.uuid4())+'.json')
                copied.write_bytes(ticket.with_name(ticket.name+'.consumed').read_bytes())
                copy_command=[*command[:-2],native_path(copied),command[-1]]
                replay=subprocess.run(copy_command,capture_output=True,text=True,encoding='utf-8',timeout=15,
                                      env=execute.runtime_environment('recording',None))
                self.assertNotIn('recording-transport',replay.stdout)
                self.assertTrue(copied.is_file())
                metadata['cases'].append('consumed-and-copied-native-ticket-zero-repeat-transport')
                for scenario in ('oversized-response','timeout-after-handle','transport-failure','exit-after-handle','exit-before-transport'):
                    result=run(scenario)
                    self.assertEqual('unknown',result['status'])
                    handles=[event for event in result['account']['events'] if event['kind']=='handle']
                    self.assertEqual(scenario in ('oversized-response','timeout-after-handle','exit-after-handle'),bool(handles))
                    if handles:
                        # Reopen through the public path, including original native proof verification.
                        recovered=execute.recover(root,resource,result['attempt'],'poll',recording_outcome='absent')
                        self.assertEqual('absent',recovered['status'])
                    with self.assertRaisesRegex(ValueError,'already dispatched or uncertain'):
                        operation.Account(root,resource).dispatch_intent(result['attempt'])
                    metadata['cases'].append('actual-native-'+scenario+'-unknown-reservation-no-resubmit')
                # Recovery reads the archived operation; editing today's contract grants no new POST.
                recoverable=run('accepted')
                authorization='authorizations/exhausted.json'
                authority.issue_recording(root,authorization,prepared,native)
                def exhausted(_):
                    return subprocess.run([sys.executable,str(Path(__file__).resolve()),'--reserve-worker',native_path(root),resource,
                                           authorization],cwd=native_path(root),capture_output=True,text=True,encoding='utf-8',timeout=60)
                with ThreadPoolExecutor(max_workers=4) as pool:
                    blocked=list(pool.map(exhausted,range(4)))
                self.assertTrue(all(result.returncode==77 for result in blocked),[result.stderr for result in blocked])
                for index,result in enumerate(blocked):
                    for stream in ('stdout','stderr'):
                        (root/f'cap-contender-{index}.{stream}.log').write_text(getattr(result,stream),encoding='utf-8')
                    metadata['processes'].append({'command':result.args,'exitCode':result.returncode})
                metadata['cases'].append('four-native-processes-original-cap-includes-all-unknown-reservations')
                configuration.write_text('{"changed":"current-input"}')
                recovered=execute.recover(root,resource,recoverable['attempt'],'poll',recording_outcome='absent')
                self.assertEqual('absent',recovered['status'])
                metadata['cases'].append('original-operation-recovery-after-current-contract-changed')
                # Verification rejects a missing prepared payload without restoring/building it.
                receipt=operation.load(root/adapter_path)
                payload=root/adapter_path;payload=payload.parent/'payload/OcrOperation.dll'
                saved=payload.read_bytes();payload.write_bytes(saved+b'changed')
                with self.assertRaisesRegex(ValueError,'payload changed'):
                    preparation.verify(root,adapter_path,operation.sha((root/adapter_path).read_bytes()))
                payload.write_bytes(saved)
                metadata['cases'].append('read-only-readiness-rejects-changed-native-payload')
                for file in account.directory.rglob('*.log'):
                    self.assertNotIn(sentinel.encode(),file.read_bytes())
                self.assertEqual(80_000,account.status(attempts[-1])['aggregateReservedMicroUsd'])
                required=json.loads((ROOT/'tests/provider-operation-cases.json').read_text())
                self.assertEqual(set(required),set(metadata['cases']))
                self.assertEqual(len(required),len(metadata['cases']))
                self.assertEqual(basis,{file.relative_to(ROOT).as_posix():operation.sha(file.read_bytes()) for file in inputs if file.is_file()})
                metadata.update(status='passed',adapterPreparation=adapter_path,nativeAdmission=native,attempts=attempts,sourceSha256=basis)
            finally:
                (root/'results.json').write_bytes(operation.canonical(metadata))
                os.chdir(previous)
                print('Retained native OCR recording proof: '+str(retained/'results.json'))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--reserve-worker':
        root=Path(sys.argv[2]);account=operation.Account(root,sys.argv[3])
        prepared=operation.contract(root,'fixtures/operation.json')
        try:
            identity=account.reserve(prepared,'provider','docs/architecture/compatibility/provider.py',
                                     sys.argv[4] if len(sys.argv)>4 else 'authorizations/one-use.json',execution='recording')
        except ValueError as error:
            if 'already consumed' not in str(error) and 'aggregate ceiling' not in str(error):raise
            raise SystemExit(77)
        print(json.dumps({'attempt':identity}))
    else:
        unittest.main()
