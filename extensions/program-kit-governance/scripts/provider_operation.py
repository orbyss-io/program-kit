"""Exact OCR-only operation binding and append-only local reservation accounting.

This module issues no human authority and has no automatic renewal or retry path.
Provider transport qualification and the existing native admission receipt remain
independent requirements. Deterministic tests use recording transports only.
"""
from __future__ import annotations
from contextlib import contextmanager, closing
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlsplit
import uuid


MAX_EVENTS = 4096
MAX_JSON = 1_048_576
ADAPTER = 'azure-document-intelligence-1.0.0-read-v1'


def root_path(root):
    from dotnet_adapter import bootstrap
    bootstrap()
    from owned_scratch import filesystem_path
    return Path(filesystem_path(Path(root).resolve()))


def require(condition, message):
    if not condition:
        raise ValueError('PKO001 ' + message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def load(path):
    require(path.is_file() and path.stat().st_size <= MAX_JSON, 'missing or oversized operation input')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'duplicate operation input member')
            value[key] = item
        return value
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('PKO001 nonfinite operation input')))


def local(root, relative):
    require(isinstance(relative, str) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', relative)
            and not {'.', '..'} & set(relative.split('/')), 'use a literal contained operation path')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()), 'operation input escaped repository')
    for ancestor in (path, *path.parents):
        if ancestor == root: break
        require(not ancestor.is_symlink() and not getattr(ancestor, 'is_junction', lambda: False)(), 'aliased operation path')
    return path


def contract(root, relative):
    """Read exact non-secret scope; request limits cannot be broadened by a transport."""
    root=root_path(root)
    path = local(root, relative)
    value = load(path)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'operation', 'adapter', 'resourceIdentity',
            'endpoint', 'fixture', 'limits', 'preparedAt', 'submitBefore', 'recoverBefore', 'credentialRef', 'account',
            'adapterPreparation'}, 'unsupported operation contract')
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 1 and value['operation'] == 'ocr-read-only'
            and value['adapter'] == ADAPTER, 'select the qualified OCR-only adapter')
    require(isinstance(value['resourceIdentity'], str) and re.fullmatch(r'/subscriptions/[A-Za-z0-9-]+/resourceGroups/[A-Za-z0-9_.-]+/providers/Microsoft.CognitiveServices/accounts/[A-Za-z0-9-]+', value['resourceIdentity'], re.I), 'bind the actual reviewed provider resource identity')
    endpoint = urlsplit(value['endpoint'])
    require(endpoint.scheme == 'https' and endpoint.hostname and endpoint.netloc == endpoint.hostname
            and not endpoint.username and not endpoint.password and endpoint.path in ('', '/') and not endpoint.query
            and not endpoint.fragment and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}\.cognitiveservices\.azure\.com', endpoint.hostname),
            'select the qualified Azure public account origin without credentials, paths or ports')
    fixture = value['fixture']
    require(isinstance(fixture, dict) and set(fixture) == {'path', 'sha256'} and isinstance(fixture['sha256'], str)
            and re.fullmatch('[0-9a-f]{64}', fixture['sha256']), 'bind the exact immutable fixture')
    input_path = local(root, fixture['path'])
    limits = value['limits']
    fields = {'submissions', 'pages', 'modelCalls', 'sdkRetries', 'fallback', 'maximumInputBytes', 'maximumResponseBytes',
              'timeoutMilliseconds', 'polls', 'pollTimeoutMilliseconds', 'deletions', 'runReservationMicroUsd', 'aggregateCeilingMicroUsd'}
    require(isinstance(limits, dict) and set(limits) == fields, 'declare the complete operation envelope')
    require(all(type(limits[key]) is int for key in fields - {'fallback'}) and limits['fallback'] is False,
            'operation limits use exact integers and forbid fallback')
    require(limits['submissions'] == 1 and limits['pages'] == 1 and limits['modelCalls'] == 0 and limits['sdkRetries'] == 0,
            'narrow admission permits one one-page OCR submission and no model call or retry')
    for key, lower, upper in [('maximumInputBytes',1,1_048_576),('maximumResponseBytes',1,1_048_576),
                              ('timeoutMilliseconds',1,60_000),('pollTimeoutMilliseconds',1,30_000),
                              ('polls',0,32),('deletions',0,1),('runReservationMicroUsd',1,10_000),
                              ('aggregateCeilingMicroUsd',1,1_000_000_000)]:
        require(lower <= limits[key] <= upper, 'unqualified operation bound: ' + key)
    require(limits['runReservationMicroUsd'] <= limits['aggregateCeilingMicroUsd'], 'reservation exceeds aggregate ceiling')
    require(input_path.is_file() and input_path.stat().st_size <= limits['maximumInputBytes'], 'fixture exceeds the admitted input limit')
    require(sha(input_path.read_bytes()) == fixture['sha256'], 'fixture changed after admission')
    require(all(type(value[key]) in (int, float) and math.isfinite(value[key]) for key in ('preparedAt','submitBefore','recoverBefore'))
            and value['preparedAt']<=time.time() and 0<value['submitBefore']-value['preparedAt']<=3600
            and 0 <= value['recoverBefore']-value['submitBefore'] <= 86_400,
            'bind finite submission and recovery deadlines within one day')
    require(isinstance(value['credentialRef'], str) and re.fullmatch('[A-Z][A-Z0-9_]{0,127}', value['credentialRef']), 'use a credential reference, never a secret value')
    account = value['account']
    require(isinstance(account,dict) and set(account)=={'identity','authorityPath','authoritySha256'}
            and isinstance(account['authoritySha256'],str) and re.fullmatch('[0-9a-f]{64}',account['authoritySha256']), 'bind original account authority and historical reservations')
    require(str(uuid.UUID(account['identity']))==account['identity'], 'invalid original account identity')
    authority_path = local(root,account['authorityPath'])
    require(authority_path.is_file() and sha(authority_path.read_bytes())==account['authoritySha256'], 'original account authority changed')
    adapter = value['adapterPreparation']
    require(isinstance(adapter,dict) and set(adapter)=={'path','sha256'} and isinstance(adapter['sha256'],str)
            and re.fullmatch('[0-9a-f]{64}',adapter['sha256']), 'bind the exact native adapter preparation')
    adapter_path = local(root,adapter['path'])
    require(adapter_path.is_file() and sha(adapter_path.read_bytes())==adapter['sha256'], 'native adapter preparation changed')
    return {'path': relative, 'sha256': sha(path.read_bytes()), 'value': value,
            'fixtureSha256': fixture['sha256'], 'resource': value['resourceIdentity'].casefold()}


def native_admission(root, prepared, prerequisite, recipe):
    """Never substitute retired bootstrap admission with newly invented spending authority."""
    raise ValueError('Bootstrap-backed provider admission is unavailable in this preview. '
                     'Preserve original account authority, reservations and uncertain outcomes. '
                     'A separately maintained current admission route is required; no provider I/O authorized.')


class Account:
    """One local resource account; missing retained state never means a fresh budget.

    SQLite transactions serialize reservation/action admission, not provider work.
    Hash chains detect malformed/deleted/reordered accounting relative to the retained
    store. This is not hostile-writer, backup-rollback or multi-host protection.
    """
    def __init__(self, root, resource):
        self.root = root_path(root)
        self.resource = resource.casefold()
        self.directory = local(self.root, 'artifacts/provider-operations/private/' + sha(self.resource.encode()))
        self.path = self.directory / 'account.sqlite'
        # Keep the original account authority outside disposable artifacts. Losing
        # a private cache cannot silently initialize a fresh aggregate budget.
        self.marker = local(self.root,'.program-kit/provider-operation-accounts/'+sha(self.resource.encode())+'.json')

    def initialize(self, ceiling, historical_reservations):
        require(type(ceiling) is int and 0 < ceiling <= 1_000_000_000, 'invalid initial aggregate ceiling')
        require(isinstance(historical_reservations,list) and len(historical_reservations)<=128, 'explicitly retain reviewed historical reservation mappings, including an explicitly empty history')
        seen = set()
        for item in historical_reservations:
            require(isinstance(item,dict) and set(item)=={'path','sha256','reservationMicroUsd'}
                    and isinstance(item['sha256'],str) and re.fullmatch('[0-9a-f]{64}',item['sha256'])
                    and type(item['reservationMicroUsd']) is int and item['reservationMicroUsd']>0
                    and item['path'] not in seen, 'invalid or duplicate original historical reservation')
            path = local(self.root,item['path'])
            require(path.is_file() and path.stat().st_size<=MAX_JSON and sha(path.read_bytes())==item['sha256'], 'original historical reservation is missing or changed')
            seen.add(item['path'])
        require(sum(item['reservationMicroUsd'] for item in historical_reservations)<=ceiling, 'historical reservations already exceed the aggregate ceiling')
        # Exclusive directory creation refuses an existing/partial account. Never
        # "repair" missing paid accounting by creating an empty replacement.
        self.directory.parent.mkdir(parents=True, exist_ok=True)
        require(not self.directory.exists() and not self.marker.exists(), 'account already exists or is incomplete; preserve and inspect it')
        self.directory.mkdir()
        self.marker.parent.mkdir(parents=True,exist_ok=True)
        from dotnet_adapter import bootstrap
        bootstrap()
        from owned_scratch import directory_identity
        identity = str(uuid.uuid4())
        marker = {'schemaVersion':1,'identity':identity,'resource':self.resource,'ceiling':ceiling,
                  'historicalReservations':historical_reservations,'directoryIdentity':list(directory_identity(self.directory))}
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript('''
                CREATE TABLE authority(payload TEXT NOT NULL);
                CREATE TABLE grants(digest TEXT PRIMARY KEY, attempt TEXT UNIQUE NOT NULL);
                CREATE TABLE events(sequence INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL);
            ''')
            connection.execute('INSERT INTO authority VALUES(?)', (canonical(marker).decode(),))
            connection.commit()
        with self.marker.open('xb') as stream:
            stream.write(canonical(marker));stream.flush()
            import os
            os.fsync(stream.fileno())
        return identity

    @contextmanager
    def transaction(self):
        require(self.directory.is_dir() and self.path.is_file() and self.marker.is_file(), 'retained account authority or reservations are missing')
        local(self.root, self.path.relative_to(self.root).as_posix())
        marker = load(self.marker)
        from dotnet_adapter import bootstrap
        bootstrap()
        from owned_scratch import native_path
        from owned_scratch import directory_identity
        require(marker['directoryIdentity']==list(directory_identity(self.directory)),
                'original account directory identity changed; copied state is historical, not fresh spending authority')
        # Extended Windows filesystem prefixes are not URI authorities. Use the
        # same physical native path and URI escaping; mode=rw still forbids reset.
        connection = sqlite3.connect(Path(native_path(self.path)).as_uri() + '?mode=rw', uri=True, timeout=5)
        try:
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('BEGIN IMMEDIATE')
            require(connection.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'account integrity check failed')
            rows = connection.execute('SELECT payload FROM authority').fetchall()
            require(len(rows)==1 and canonical(marker).decode()==rows[0][0] and marker['resource']==self.resource, 'account authority changed')
            for item in marker['historicalReservations']:
                original = local(self.root,item['path'])
                require(original.is_file() and original.stat().st_size<=MAX_JSON and sha(original.read_bytes())==item['sha256'],
                        'original historical reservation is missing or changed; its charge cannot disappear')
            events = connection.execute('SELECT sequence,payload,previous,digest FROM events ORDER BY sequence').fetchall()
            require(len(events) <= MAX_EVENTS, 'account history capacity exhausted; no history is discarded')
            sequence = connection.execute("SELECT seq FROM sqlite_sequence WHERE name='events'").fetchall()
            require(sequence == ([(len(events),)] if events else []), 'account reservations/events were removed')
            previous = '0'*64
            values = []
            for index, payload, prior, digest in events:
                require(index == len(values)+1 and prior == previous and sha((prior+'\n'+payload).encode()) == digest,
                        'account history changed or lost an event')
                event = json.loads(payload)
                require(isinstance(event,dict) and canonical(event).decode()==payload, 'noncanonical account event')
                require(event.get('kind') in {'reserved','dispatch-intent','handle','submission-outcome',
                                              'recovery-intent','recovery-outcome'}, 'unknown account event')
                values.append(event); previous = digest
            reservations = [event for event in values if event.get('kind')=='reserved']
            grants = connection.execute('SELECT digest,attempt FROM grants ORDER BY digest').fetchall()
            require(grants == sorted((event['grant']['sha256'],event['attempt']) for event in reservations)
                    and len({event['attempt'] for event in reservations}) == len(reservations), 'missing or duplicate reservation/grant binding')
            yield connection, marker, values, previous
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def append(connection, events, previous, event):
        require(len(events) < MAX_EVENTS, 'account history capacity exhausted; no new effect admitted')
        payload = canonical(event).decode()
        require(len(payload.encode()) <= MAX_JSON, 'oversized account event')
        connection.execute('INSERT INTO events(payload,previous,digest) VALUES(?,?,?)',
                           (payload,previous,sha((previous+'\n'+payload).encode())))

    def reserve(self, prepared, prerequisite, recipe, authorization_path, *, execution):
        from provider_operation_authority import read as read_authority
        refreshed = contract(self.root, prepared['path'])
        require(refreshed == prepared, 'operation inputs changed after preparation')
        native = native_admission(self.root, refreshed, prerequisite, recipe)
        grant = read_authority(self.root,authorization_path,prepared,native,execution)
        require(prepared['resource'] == self.resource, 'native authority selected a different provider resource')
        limits = prepared['value']['limits']
        attempt = str(uuid.uuid4())
        with self.transaction() as (connection, marker, events, previous):
            require(native_admission(self.root, refreshed, prerequisite, recipe) == native
                    and read_authority(self.root,authorization_path,prepared,native,execution)==grant,
                    'native admission changed while waiting for reservation')
            require(time.time() < prepared['value']['submitBefore'], 'submission authority expired while waiting for reservation')
            reservations = [event for event in events if event['kind']=='reserved']
            require(prepared['value']['account']=={'identity':marker['identity'],
                    'authorityPath':self.marker.relative_to(self.root).as_posix(),'authoritySha256':sha(self.marker.read_bytes())},
                    'operation admission selected a different original resource account')
            ceiling = min([marker['ceiling'],limits['aggregateCeilingMicroUsd']]
                          + [event['ceiling'] for event in reservations])
            historical = sum(item['reservationMicroUsd'] for item in marker['historicalReservations'])
            require(historical+sum(event['reservation'] for event in reservations)+limits['runReservationMicroUsd'] <= ceiling,
                    'all retained reservations including unknown outcomes exceed the original aggregate ceiling')
            capacity = 4+2*(limits['polls']+limits['deletions'])
            require(sum(event['eventCapacity'] for event in reservations)+capacity<=MAX_EVENTS,
                    'finite accounting capacity cannot admit this attempt and retain all its recovery outcomes')
            require(not any(event['grant']['sha256']==grant['sha256'] for event in reservations), 'native authority already consumed; no automatic retry')
            event = {'kind':'reserved','attempt':attempt,'grant':grant,'contract':prepared['path'],
                     'prerequisite':prerequisite,'recipe':recipe,
                     'contractSha256':prepared['sha256'],'fixtureSha256':prepared['fixtureSha256'],
                     'reservation':limits['runReservationMicroUsd'],'ceiling':ceiling,
                     'eventCapacity':capacity,
                     'submitBefore':prepared['value']['submitBefore'],'recoverBefore':prepared['value']['recoverBefore']}
            connection.execute('INSERT INTO grants VALUES(?,?)',(grant['sha256'],attempt))
            archive = self.directory / 'contracts'
            archive.mkdir(exist_ok=True)
            source_bytes = local(self.root, prepared['path']).read_bytes()
            require(sha(source_bytes) == prepared['sha256'], 'operation contract changed before reservation')
            original = archive / (prepared['sha256']+'.json')
            if original.exists():
                require(original.read_bytes()==source_bytes, 'retained original operation contract changed')
            else:
                with original.open('xb') as stream:
                    stream.write(source_bytes); stream.flush()
                    import os
                    os.fsync(stream.fileno())
            self.append(connection,events,previous,event)
        return attempt

    @staticmethod
    def attempt(events, identity):
        selected = [event for event in events if event.get('attempt') == identity]
        require(selected and selected[0]['kind']=='reserved' and sum(event['kind']=='reserved' for event in selected)==1,
                'missing or duplicate original attempt reservation')
        return selected

    def original(self, reservation):
        path = self.directory/'contracts'/(reservation['contractSha256']+'.json')
        require(path.is_file() and sha(path.read_bytes())==reservation['contractSha256'], 'original operation contract is missing or changed')
        value = load(path)
        require(value['resourceIdentity'].casefold()==self.resource and value['fixture']['sha256']==reservation['fixtureSha256'],
                'original operation identity changed')
        return value

    def historical_admission(self, reservation):
        """Cleanup consumes the original native proof, never fresh submission authority."""
        from dotnet_adapter import bootstrap
        bootstrap()
        from test_results import test_results
        grant = reservation['grant']
        authorization = local(self.root,grant['path'])
        require(authorization.is_file() and sha(authorization.read_bytes())==grant['sha256'], 'original one-use provider authority changed')
        native = grant['nativeAdmission']
        path = local(self.root,native['path'])
        require(path.is_file() and sha(path.read_bytes())==native['sha256'], 'original native admission changed')
        proof = load(path)
        require(proof.get('schema_version') in ('1.1','1.2') and proof.get('exit_code')==0
                and proof.get('process_exit_code')==0 and proof.get('prerequisite')==reservation['prerequisite'],
                'original native admission did not succeed')
        require({(reservation['contract'],reservation['contractSha256'])} <=
                {(item['path'],item['sha256']) for item in proof['inputs']}, 'original native admission binding changed')
        record = proof['test_result']
        report = local(self.root,record['path'])
        require(report.resolve().is_relative_to(path.parent.resolve()) and sha(report.read_bytes())==record['sha256'],
                'original native admission test evidence changed')
        actual = test_results(report,'junit')
        require(proof['checks'] and all(actual.values()) and all(actual.get(name) is True for name in proof['checks']),
                'original native admission required cases are incomplete')

    def dispatch_intent(self, identity):
        started = time.monotonic()
        from provider_operation_authority import read as read_authority
        with self.transaction() as (connection, marker, events, previous):
            attempt = self.attempt(events,identity)
            require(len(attempt)==1, 'attempt already dispatched or uncertain; recovery never resubmits')
            reservation = attempt[0]
            prepared = contract(self.root,reservation['contract'])
            require(prepared['sha256']==reservation['contractSha256'] and prepared['fixtureSha256']==reservation['fixtureSha256'],
                    'admitted operation inputs changed')
            native = native_admission(self.root,prepared,reservation['prerequisite'],reservation['recipe'])
            require(read_authority(self.root,reservation['grant']['path'],prepared,native,reservation['grant']['execution'])==reservation['grant'],
                    'current native admission differs from this one-use reservation')
            limits = prepared['value']['limits']
            remaining = min((reservation['submitBefore']-time.time())*1000,
                            limits['timeoutMilliseconds']-(time.monotonic()-started)*1000)
            require(remaining>0, 'submission expired while waiting for final dispatch admission')
            self.append(connection,events,previous,{'kind':'dispatch-intent','attempt':identity,'at':time.time()})
            prepared['dispatchDeadlineMonotonic']=started+limits['timeoutMilliseconds']/1000
        return prepared, max(1,int(remaining))

    def retain_handle(self, identity, handle):
        require(isinstance(handle,str) and str(uuid.UUID(handle))==handle, 'invalid provider operation handle')
        with self.transaction() as (connection, marker, events, previous):
            attempt = self.attempt(events,identity)
            require(any(event['kind']=='dispatch-intent' for event in attempt), 'handle has no original dispatch')
            existing = [event['handle'] for event in attempt if event['kind']=='handle']
            require(not existing or existing==[handle], 'provider operation handle changed')
            if not existing:
                self.append(connection,events,previous,{'kind':'handle','attempt':identity,'handle':handle})

    def submission_outcome(self, identity, status):
        require(status in ('acknowledged','unknown','unavailable'), 'unsupported submission outcome')
        with self.transaction() as (connection, marker, events, previous):
            attempt = self.attempt(events,identity)
            require(any(event['kind']=='dispatch-intent' for event in attempt)
                    and not any(event['kind']=='submission-outcome' for event in attempt), 'submission outcome is absent or already sealed')
            require(status!='acknowledged' or any(event['kind']=='handle' for event in attempt), 'acknowledgement requires its actual retained handle')
            self.append(connection,events,previous,{'kind':'submission-outcome','attempt':identity,'status':status})

    def recovery_intent(self, identity, action):
        started=time.monotonic()
        require(action in ('poll','delete'), 'recovery cannot submit/model/fallback/retry')
        with self.transaction() as (connection, marker, events, previous):
            attempt = self.attempt(events,identity)
            reservation = attempt[0]
            value = self.original(reservation)
            self.historical_admission(reservation)
            handles = [event['handle'] for event in attempt if event['kind']=='handle']
            require(len(handles)==1, 'unknown submission has no owned handle; retain its reservation and investigate without resubmission')
            require(time.time()<value['recoverBefore'], 'original bounded recovery permission expired')
            require(not any(event['kind']=='recovery-outcome' and event['status']=='absent' for event in attempt),
                    'result absence was already observed; no new cleanup or paid authority')
            intents = [event for event in attempt if event['kind']=='recovery-intent']
            completed = {event['intent'] for event in attempt if event['kind']=='recovery-outcome'}
            require(all(event['id'] in completed or time.time()>=event['at']+value['limits']['pollTimeoutMilliseconds']/1000
                        for event in intents), 'an owned recovery action is still within its original deadline')
            maximum = value['limits']['polls' if action=='poll' else 'deletions']
            require(sum(event['action']==action for event in intents)<maximum, 'original recovery action limit exhausted; authority is not renewed')
            token = str(uuid.uuid4())
            self.append(connection,events,previous,{'kind':'recovery-intent','attempt':identity,'action':action,'id':token,'at':time.time()})
            value['_recoveryDeadlineMonotonic']=started+value['limits']['pollTimeoutMilliseconds']/1000
        return value,handles[0],token

    def recovery_outcome(self, identity, token, status, response_sha256=None):
        require(status in ('running','succeeded','failed','absent','unknown'), 'unsupported recovery observation')
        require(response_sha256 is None or isinstance(response_sha256,str) and re.fullmatch('[0-9a-f]{64}',response_sha256),
                'record only bounded response identity, not private result text')
        with self.transaction() as (connection, marker, events, previous):
            attempt = self.attempt(events,identity)
            intents = [event for event in attempt if event['kind']=='recovery-intent' and event['id']==token]
            require(len(intents)==1 and not any(event['kind']=='recovery-outcome' and event['intent']==token for event in attempt),
                    'unknown or already completed recovery action')
            # A successful DELETE acknowledgement never proves absence. Only a
            # separately scoped GET/observation may record that provider fact.
            require(intents[0]['action']!='delete' or status=='unknown', 'deletion acknowledgement is not observed result absence')
            self.append(connection,events,previous,{'kind':'recovery-outcome','attempt':identity,'intent':token,
                                                   'status':status,'responseSha256':response_sha256})

    def status(self, identity):
        with self.transaction() as (_, marker, events, previous):
            attempt = self.attempt(events,identity)
            return {'attempt':identity,'reservationMicroUsd':attempt[0]['reservation'],
                    'aggregateReservedMicroUsd':sum(event['reservation'] for event in events if event['kind']=='reserved')
                        + sum(item['reservationMicroUsd'] for item in marker['historicalReservations']),
                    'events':attempt,'headSha256':previous,'scope':'OCR-only operation; no combined model/provider or application acceptance'}

    def review(self):
        """Read retained totals before human confirmation; no reservation or refund."""
        with self.transaction() as (_,marker,events,previous):
            reservations=[event for event in events if event['kind']=='reserved']
            return {'identity':marker['identity'],'resource':self.resource,
                    'originalCeilingMicroUsd':min([marker['ceiling']]+[event['ceiling'] for event in reservations]),
                    'aggregateReservedMicroUsd':sum(event['reservation'] for event in reservations)
                        +sum(item['reservationMicroUsd'] for item in marker['historicalReservations']),
                    'originalHistoricalReservations':marker['historicalReservations'],
                    'attempts':[self.attempt(events,event['attempt']) for event in reservations],
                    'headSha256':previous}
