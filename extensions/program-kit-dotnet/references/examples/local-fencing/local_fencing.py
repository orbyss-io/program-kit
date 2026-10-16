"""Synthetic local-file fencing recipe, not a general storage/outbox implementation.

Cooperating processes on one local host only. No power-loss, hostile-writer,
network-volume, paid-operation or consumer business-policy guarantee is supplied.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
import uuid

MAX_CONTENT = 1_048_576
MAX_COUNTER = 9_223_372_036_854_775_807
MAX_JOURNAL = 64
TICKET_FIELDS = {'resource', 'work', 'operation', 'action', 'fence', 'payload', 'deadline'}


class Denied(ValueError):
    pass


class Unavailable(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise Denied(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def pairs(rows):
    value = {}
    for key, item in rows:
        require(key not in value, 'Duplicate authority field; preserve evidence, do not reset.')
        value[key] = item
    return value


def document(path):
    regular(path)
    require(path.stat().st_size <= 65_536, 'Authority record exceeds its finite budget.')
    return json.loads(path.read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, 'Non-finite authority value.'))


def regular(path, missing=False):
    path = Path(path)
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            require(missing and part == path, 'Missing retained authority/input: '+str(path.name))
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400), 'Linked resource paths are not admitted.')
    if path.exists():
        require(path.is_file(), 'Expected a regular local resource file.')


def atomic(path, value):
    raw = canonical(value)
    require(len(raw) <= 65_536, 'Authority journal is full; no implicit retention retirement.')
    temporary = path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ticket_identity(ticket):
    require(isinstance(ticket, dict) and set(ticket) == TICKET_FIELDS, 'Use the exact committed work envelope.')
    require(type(ticket['fence']) is int and 0 < ticket['fence'] <= MAX_COUNTER
            and type(ticket['deadline']) is int and 0 < ticket['deadline'] <= MAX_COUNTER, 'Invalid fence/deadline; no reset-to-zero.')
    require(all(isinstance(ticket[key], str) and re.fullmatch('[a-z0-9-]{1,64}', ticket[key]) for key in ('resource', 'work', 'operation')),
            'Use bounded opaque work/resource identities.')
    require(ticket['action'] in {'publish', 'erase', 'reconcile'}, 'Unknown physical authority.')
    require(ticket['payload'] is None if ticket['action'] != 'publish' else isinstance(ticket['payload'], str)
            and re.fullmatch('[0-9a-f]{64}', ticket['payload']), 'Exact payload identity is required only for publication.')
    return digest(canonical(ticket))


class WorkStore:
    """A committed SQLite intent is the fixture's explicit authority source."""
    def __init__(self, root, resource):
        self.path = Path(root)/'work.sqlite'; self.resource = resource

    @contextmanager
    def connect(self):
        regular(self.path)
        connection = sqlite3.connect(self.path.as_uri()+'?mode=rw', uri=True, timeout=0.1)
        try:
            require(connection.execute("select value from metadata where name='resource'").fetchall() == [(self.resource,)],
                    'Work store/resource identity differs; no recreated authority.')
            with connection:
                yield connection
        finally:
            connection.close()

    def issue(self, work, operation, action, payload=None, *, deadline=None):
        deadline = deadline if deadline is not None else time.time_ns()+30_000_000_000
        with self.connect() as connection:
            connection.execute('begin immediate')
            previous = connection.execute('select action,payload from work where work=? and operation=?', (work, operation)).fetchall()
            require(all(row == (action, payload) for row in previous), 'Conflicting operation reuse is not a new execution.')
            cursor = connection.execute('insert into work(work,operation,action,payload,deadline,status) values(?,?,?,?,?,?)',
                                        (work, operation, action, payload, deadline, 'committed'))
            ticket = dict(resource=self.resource, work=work, operation=operation, action=action,
                          payload=payload, deadline=deadline, fence=cursor.lastrowid)
            ticket_identity(ticket)
        return ticket  # Never return a fence until its intent transaction commits.

    def validate(self, ticket):
        ticket_identity(ticket)
        require(ticket['resource'] == self.resource, 'Different resource identity cannot reset authority.')
        with self.connect() as connection:
            rows = connection.execute('select work,operation,action,payload,deadline,status from work where fence=?', (ticket['fence'],)).fetchall()
        expected = tuple(ticket[key] for key in ('work', 'operation', 'action', 'payload', 'deadline'))
        require(len(rows) == 1 and rows[0][:-1] == expected and rows[0][-1] in {'committed', 'completed'},
                'Missing/corrupt/uncommitted physical work authority.')

    def complete(self, ticket):
        self.validate(ticket)
        with self.connect() as connection:
            connection.execute("update work set status='completed' where fence=?", (ticket['fence'],))

    def status(self, fence):
        with self.connect() as connection:
            return connection.execute('select status from work where fence=?', (fence,)).fetchone()[0]


class Resource:
    def __init__(self, root, *, clock=time.time_ns, cancelled=lambda _: False, on_guard_wait=lambda _: None):
        self.root = Path(root).absolute()
        marker = document(self.root/'resource.json')
        require(set(marker) == {'recipe', 'resource'} and marker['recipe'] == 'program-kit-local-fencing-v1', 'Not a provisioned synthetic resource.')
        self.resource = marker['resource']; self.store = WorkStore(self.root, self.resource); self.clock = clock; self.cancelled = cancelled
        self.on_guard_wait = on_guard_wait
        self.authority = self.root/'authority.json'; self.payload = self.root/'payload.bin'

    @staticmethod
    def provision(root):
        root = Path(root).absolute()
        root.mkdir()  # A previous/missing/corrupt resource can never be reprovisioned in place.
        resource = uuid.uuid4().hex
        atomic(root/'resource.json', dict(recipe='program-kit-local-fencing-v1', resource=resource))
        (root/'guard.lock').write_bytes(b'0')
        (root/'staging').mkdir(); (root/'control').mkdir()
        connection = sqlite3.connect(root/'work.sqlite')
        with connection:
            connection.execute('create table metadata(name text primary key,value text not null)')
            connection.execute('insert into metadata values(?,?)', ('resource', resource))
            connection.execute('create table work(fence integer primary key autoincrement,work text not null,operation text not null,action text not null,payload text,deadline integer not null,status text not null)')
        connection.close()
        atomic(root/'authority.json', dict(schemaVersion=1, resource=resource, highWater=0, owner=None,
                                          barrier=False, effect=None, observation=None, journal=[]))
        return Resource(root)

    def checkpoint(self, ticket):
        require(not self.cancelled(ticket), 'Observed cancellation of this exact work fence; no new physical effect.')
        require(self.clock() < ticket['deadline'], 'Lease expired, including deadline equality; no physical authority.')

    @contextmanager
    def guard(self, deadline, ticket=None):
        path = self.root/'guard.lock'; regular(path)
        with path.open('r+b', buffering=0) as stream:
            acquired = False
            try:
                while not acquired:
                    require(self.clock() < deadline, 'Lease expired while waiting for the physical guard.')
                    if ticket is not None: self.checkpoint(ticket)
                    try:
                        stream.seek(0)
                        if os.name == 'nt':
                            import msvcrt
                            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                    except OSError as error:
                        import errno
                        if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                            raise
                        if ticket is not None: self.on_guard_wait(ticket)
                        time.sleep(0.005)
                require(self.clock() < deadline, 'Lease expired after physical guard wait.')
                if ticket is not None: self.checkpoint(ticket)
                yield
            finally:
                if acquired:
                    stream.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def state(self):
        value = document(self.authority)
        require(set(value) == {'schemaVersion', 'resource', 'highWater', 'owner', 'barrier', 'effect', 'observation', 'journal'}
                and type(value['schemaVersion']) is int and value['schemaVersion'] == 1 and value['resource'] == self.resource
                and type(value['highWater']) is int and 0 <= value['highWater'] <= MAX_COUNTER
                and type(value['barrier']) is bool and isinstance(value['journal'], list) and len(value['journal']) <= MAX_JOURNAL,
                'Corrupt/ambiguous retained fence authority; preserve evidence, do not reset.')
        if value['owner'] is not None:
            ticket_identity(value['owner'])
            require(value['owner']['fence'] == value['highWater'] and value['owner']['resource'] == self.resource, 'High-water owner differs.')
        else:
            require(value['highWater'] == 0 and not value['barrier'] and value['effect'] is None, 'Missing high-water identity.')
        previous = 0
        for row in value['journal']:
            require(isinstance(row, dict) and set(row) == {'fence', 'work', 'operation'} and type(row['fence']) is int
                    and previous < row['fence'] <= value['highWater'], 'Duplicate/corrupt/nonmonotonic retained admission.')
            previous = row['fence']
        require(previous == value['highWater'] and (not value['journal'] or all(value['journal'][-1][key] == value['owner'][key] for key in ('work', 'operation'))),
                'Retained journal does not bind the current high-water identity.')
        if value['effect'] is not None:
            effect = value['effect']
            require(isinstance(effect, dict) and set(effect) == {'ticket', 'phase', 'previous'}
                    and effect['phase'] in {'intent', 'completed', 'not-observed'}
                    and (effect['previous'] is None or isinstance(effect['previous'], str) and re.fullmatch('[0-9a-f]{64}', effect['previous'])),
                    'Corrupt retained effect intent.')
            self.store.validate(effect['ticket'])
            require(effect['ticket']['fence'] <= value['highWater'] and effect['ticket']['action'] in {'publish', 'erase'}
                    and (effect['ticket']['action'] != 'erase' or value['barrier']), 'Corrupt effect fence/removal barrier.')
        require(not value['barrier'] or value['effect'] is not None and value['effect']['ticket']['action'] == 'erase', 'Missing retained removal identity.')
        return value

    def require_owner(self, state, ticket, action=None):
        self.store.validate(ticket); self.checkpoint(ticket)
        require(state['highWater'] == ticket['fence'] and state['owner'] == ticket, 'Stale/mismatched fence cannot publish, read for recovery or erase.')
        require(action is None or ticket['action'] == action, 'Wrong committed physical operation.')

    def physical(self):
        regular(self.payload, missing=True)
        if not self.payload.exists():
            return None
        require(self.payload.stat().st_size <= MAX_CONTENT, 'Synthetic payload exceeds the reference scope.')
        with self.payload.open('rb') as stream:
            content = stream.read(MAX_CONTENT+1)
        require(len(content) <= MAX_CONTENT, 'Synthetic payload grew beyond its finite budget.')
        return digest(content)

    def admit(self, ticket, fault=None):
        self.store.validate(ticket); self.checkpoint(ticket)
        with self.guard(ticket['deadline'], ticket):
            state = self.state(); self.store.validate(ticket); self.checkpoint(ticket)
            require(ticket['fence'] >= state['highWater'], 'A lower fence cannot reclaim physical authority.')
            require(not state['barrier'] or ticket['action'] != 'publish', 'Retained removal barrier prevents resurrection.')
            if ticket['fence'] == state['highWater']:
                require(state['owner'] == ticket, 'Same counter with a different identity is not replay.')
                return 'already-admitted'
            require(not state['effect'] or state['effect']['phase'] != 'intent' or ticket['action'] == 'reconcile',
                    'Uncertain physical effect needs observed reconciliation before new mutation.')
            require(len(state['journal']) < MAX_JOURNAL, 'Retained fence journal is full; no automatic retirement.')
            state.update(highWater=ticket['fence'], owner=ticket, observation=None)
            state['journal'].append({'fence': ticket['fence'], 'work': ticket['work'], 'operation': ticket['operation']})
            atomic(self.authority, state)
            if fault == 'after-admission': os._exit(91)
            return 'admitted'

    def stage(self, ticket, content):
        self.store.validate(ticket); self.checkpoint(ticket)
        require(ticket['action'] == 'publish' and len(content) <= MAX_CONTENT and digest(content) == ticket['payload'], 'Stage only the exact committed synthetic payload.')
        relative = f'staging/{ticket["fence"]}-{ticket["operation"]}-{uuid.uuid4().hex}.part'
        path = self.root/relative
        regular(path, missing=True)
        with path.open('xb') as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        return relative

    def owned_stage(self, ticket, relative):
        require(isinstance(relative, str) and re.fullmatch(r'staging/'+str(ticket['fence'])+'-'+re.escape(ticket['operation'])+r'-[0-9a-f]{32}\.part', relative),
                'Cleanup/publication must name only this work attempt\'s exact owned staging.')
        path = self.root/relative; regular(path, missing=True)
        return path

    def effect(self, ticket, stage=None, fault=None):
        self.store.validate(ticket)
        require(ticket.get('action') in {'publish', 'erase'}, 'Physical mutation requires committed publish/erase authority.')
        owned = self.owned_stage(ticket, stage) if stage is not None else None
        try:
            with self.guard(ticket['deadline'], ticket):
                state = self.state(); self.require_owner(state, ticket)
                current = self.physical(); self.checkpoint(ticket)
                if state['effect'] and state['effect']['phase'] == 'intent':
                    raise Unavailable('Effect intent is uncertain; observe and reconcile, never blind resubmit.')
                if state['effect'] and state['effect']['ticket'] == ticket:
                    expected = ticket['payload'] if ticket['action'] == 'publish' else None
                    require(current == expected and state['effect']['phase'] == 'completed', 'Completed replay differs from physical state.')
                    self.store.complete(ticket)
                    return 'replayed'
                if ticket['action'] == 'publish':
                    require(not state['barrier'] and owned is not None and owned.is_file()
                            and owned.stat().st_size <= MAX_CONTENT, 'Missing/oversized staging or retained removal barrier.')
                    with owned.open('rb') as stream:
                        content = stream.read(MAX_CONTENT+1)
                    require(len(content) <= MAX_CONTENT and digest(content) == ticket['payload'], 'Changed owned staging input.')
                    self.checkpoint(ticket)
                intent = dict(ticket=ticket, phase='intent', previous=current)
                state.update(effect=intent, observation=None, barrier=state['barrier'] or ticket['action'] == 'erase')
                atomic(self.authority, state)
                if fault == 'after-intent': os._exit(91)
                self.checkpoint(ticket)  # Recheck after the persisted intent/input wait.
                if ticket['action'] == 'publish': os.replace(owned, self.payload)
                else: self.payload.unlink(missing_ok=True)
                if fault == 'after-effect': os._exit(91)
                self.checkpoint(ticket)
                state['effect']['phase'] = 'completed'; atomic(self.authority, state)
                if fault == 'after-completion': os._exit(91)
                self.store.complete(ticket)
                return 'completed'
        finally:
            if owned is not None:
                # Never clean another fence's staging or remove retained metadata.
                self.owned_stage(ticket, stage).unlink(missing_ok=True)

    def observe(self, ticket):
        with self.guard(ticket['deadline'], ticket):
            state = self.state(); self.require_owner(state, ticket)
            require(ticket['action'] == 'reconcile', 'A lease-driven recovery read needs committed reconciliation authority.')
            observation = dict(owner=ticket_identity(ticket), payload=self.physical(), effect=digest(canonical(state['effect'])), barrier=state['barrier'])
            self.checkpoint(ticket)
            state['observation'] = observation; atomic(self.authority, state)
            return observation

    def reconcile(self, ticket, observation):
        with self.guard(ticket['deadline'], ticket):
            state = self.state(); self.require_owner(state, ticket, 'reconcile')
            actual = dict(owner=ticket_identity(ticket), payload=self.physical(), effect=digest(canonical(state['effect'])), barrier=state['barrier'])
            self.checkpoint(ticket)
            require(observation == actual == state['observation'], 'Recovery observation is stale or not authority-bound.')
            effect = state['effect']
            require(effect is not None, 'No committed physical intent to reconcile.')
            expected = effect['ticket']['payload'] if effect['ticket']['action'] == 'publish' else None
            if actual['payload'] == expected:
                effect['phase'] = 'completed'; outcome = 'observed-completed'
                self.store.complete(effect['ticket'])
            elif actual['payload'] == effect['previous'] and effect['phase'] == 'intent':
                effect['phase'] = 'not-observed'; outcome = 'observed-not-applied'
            else:
                raise Unavailable('Physical effect conflicts with both expected and prior state; preserve uncertainty.')
            state['observation'] = None; atomic(self.authority, state)
            self.store.complete(ticket)
            return outcome

    def inspect(self):
        # Ordinary inspection grants no mutation/reconciliation authority.
        with self.guard(self.clock()+5_000_000_000):
            return dict(state=self.state(), payload=self.physical(), authorityGranted=False)

    def legacy_publish(self, *_): raise Denied('Unfenced publication has no protected physical authority.')
    def legacy_erase(self, *_): raise Denied('Unfenced removal has no protected physical authority.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    request = document(args.request)
    resource = Resource(args.root,
                        cancelled=lambda ticket: (args.root/'control'/('cancel-'+str(ticket['fence']))).is_file(),
                        on_guard_wait=lambda ticket: atomic(args.root/'control'/('waiting-'+str(ticket['fence'])), {'phase': 'contended'}))
    method = request['method']; ticket = request.get('ticket')
    if method == 'hold':
        with resource.guard(resource.clock()+10_000_000_000):
            atomic(resource.root/'control/ready', {'phase': 'guard-held'})
            while not (resource.root/'control/release').exists():
                require(resource.clock() < request['deadline'], 'Synthetic hold deadline expired.')
                time.sleep(0.005)
        result = 'released'
    elif method == 'publish':
        stage = resource.stage(ticket, bytes.fromhex(request['contentHex']))
        if request.get('pause'):
            atomic(resource.root/'control/ready', {'stage': stage})
            while not (resource.root/'control/release').exists():
                require(resource.clock() < request['pauseDeadline'], 'Synthetic pause deadline expired.')
                time.sleep(0.005)
        result = resource.effect(ticket, stage, request.get('fault'))
    elif method == 'erase':
        if request.get('pause'):
            atomic(resource.root/'control/ready', {'phase': 'erase-wait'})
            while not (resource.root/'control/release').exists():
                require(resource.clock() < request['pauseDeadline'], 'Synthetic pause deadline expired.')
                time.sleep(0.005)
        result = resource.effect(ticket, fault=request.get('fault'))
    elif method == 'admit': result = resource.admit(ticket, request.get('fault'))
    elif method == 'observe': result = resource.observe(ticket)
    elif method == 'reconcile': result = resource.reconcile(ticket, request['observation'])
    elif method == 'inspect': result = resource.inspect()
    else: raise Denied('Unknown synthetic reference operation.')
    print(json.dumps({'status': 'completed', 'result': result}))


if __name__ == '__main__':
    main()
