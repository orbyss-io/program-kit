"""Independent public HTTP oracle for the fictional equipment-lending fixture.

The harness supplies a real host restart callback. The application cannot attest
its own restart. Test-only snapshots observe effects; decisions use the public API.
No coding agent, registry operation or consumer source import occurs here.
"""
from __future__ import annotations

import copy
import json
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, OpenerDirector, ProxyHandler, HTTPHandler, HTTPDefaultErrorHandler, HTTPErrorProcessor

from .common import LiveContractError


class LendingOracle:
    def __init__(self, base_url, restart, contract):
        url = urlparse(base_url)
        if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'} or url.username or url.password or url.path not in {'', '/'}:
            raise LiveContractError('LENDING_ORACLE_DISPOSABLE_LOOPBACK_REQUIRED')
        if not callable(restart):
            raise LiveContractError('LENDING_ORACLE_REAL_RESTART_REQUIRED')
        self.base = base_url.rstrip('/')
        self.restart = restart
        self.contract = contract
        self.checks = []
        self.exchanges = []
        # The fixture is HTTP loopback only. Do not install HTTPS or redirect
        # handlers that could turn a consumer response into an external request.
        self.client = OpenerDirector()
        for handler in (ProxyHandler({}), HTTPHandler(), HTTPDefaultErrorHandler(), HTTPErrorProcessor()):
            self.client.add_handler(handler)

    def require(self, condition, name):
        if not condition:
            raise LiveContractError('LENDING_ORACLE_FAILED: ' + name)

    def request(self, method, path, body=None, *, raw=None):
        data = raw.encode('utf-8') if raw is not None else json.dumps(body).encode('utf-8') if body is not None else None
        request = Request(self.base + path, data=data, method=method,
                          headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            response = self.client.open(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            status, content = response.status, response.read(1024 * 1024 + 1)
        self.require(len(content) <= 1024 * 1024, 'bounded-public-response')
        try:
            value = json.loads(content) if content else None
        except ValueError:
            raise LiveContractError('LENDING_ORACLE_NON_JSON_RESPONSE: ' + path)
        self.exchanges.append({'method': method, 'path': path, 'request': body if raw is None else raw,
                               'status': status, 'response': value})
        return status, value

    def control(self, operation):
        method = 'GET' if operation == 'snapshot' else 'POST'
        status, body = self.request(method, self.contract['testOnlyControl']['prefix'] + '/' + operation)
        self.require(status == 200, 'fixture-control-' + operation)
        if operation == 'snapshot':
            self.require(isinstance(body, dict) and set(self.contract['testOnlyControl']['snapshotFields']) <= set(body), 'complete-effect-snapshot')
        return body

    def public(self, operation, body=None, identity=None, *, raw=None):
        definition = self.contract[operation]
        path = self.contract['publicPrefix'] + definition['path']
        if identity is not None:
            path = path.replace('{reservationId}', str(identity))
        return self.request(definition['method'], path, body, raw=raw)

    def completed(self, name):
        self.checks.append({'id': name, 'status': 'passed', 'lastExchange': len(self.exchanges)})

    def run(self):
        codes = self.contract['statusCodes']
        self.control('reset')
        pristine = self.control('snapshot')
        self.require(pristine['available'] == self.contract['equipment']['initialCapacity'], 'initial-capacity')
        reserve = copy.deepcopy(self.contract['reserve']['body'])

        # Unknown/duplicate members and coercion must be rejected before effects.
        for payload in (json.dumps({**reserve, 'unknown': True}),
                        json.dumps({**reserve, 'quantity': '1'}),
                        json.dumps(reserve)[:-1] + ', "quantity": 2}'):
            status, _ = self.public('reserve', raw=payload)
            self.require(status == codes['invalidAdmission'], 'strict-typed-v1-admission')
            self.require(self.control('snapshot') == pristine, 'invalid-admission-no-effects')
        self.completed('typed-v1-admission')

        denied = {**reserve, 'operationId': 'fixture-denied', 'quantity': pristine['available'] + 1}
        status, _ = self.public('reserve', denied)
        self.require(status == codes['conflictOrDenied'] and self.control('snapshot') == pristine, 'policy-before-effects')
        self.completed('policies-before-effects')

        status, first = self.public('reserve', reserve)
        self.require(status == codes['created'] and isinstance(first, dict), 'reservation-created')
        fields = set(self.contract['reservation']['fields'])
        self.require(fields <= set(first) and first['state'] == 'Reserved' and first['operationId'] == reserve['operationId']
                     and first['equipmentId'] == reserve['equipmentId'] and first['quantity'] == reserve['quantity'], 'v1-wire-shape')
        identity = first['reservationId']
        self.require(isinstance(identity, str) and bool(identity), 'public-reservation-identity')
        reserved = self.control('snapshot')
        self.require(reserved['available'] == pristine['available'] - 1, 'single-reservation-effect')
        status, replay = self.public('reserve', reserve)
        self.require(status == codes['replay'] and replay == first and self.control('snapshot') == reserved, 'idempotent-replay')
        status, _ = self.public('reserve', {**reserve, 'quantity': 2})
        self.require(status == codes['conflictOrDenied'] and self.control('snapshot') == reserved, 'idempotency-content-conflict')
        self.completed('idempotent-admission')

        restart_evidence = self.restart()
        self.require(isinstance(restart_evidence, dict) and restart_evidence.get('stopped') is True
                     and restart_evidence.get('sameDataDirectory') is True
                     and restart_evidence.get('beforeProcessId') != restart_evidence.get('afterProcessId')
                     and all(type(restart_evidence.get(k)) is int and restart_evidence[k] > 0 for k in ('beforeProcessId', 'afterProcessId')), 'observed-process-restart')
        status, recovered = self.public('reservation', identity=identity)
        self.require(status == 200 and recovered == first and self.control('snapshot') == reserved, 'durable-restart-preserves-identity')
        self.completed('durable-restart')

        confirm = copy.deepcopy(self.contract['confirm']['body'])
        status, _ = self.public('confirm', {**confirm, 'acknowledged': False}, identity)
        self.require(status == codes['invalidAdmission'] and self.control('snapshot') == reserved, 'explicit-acknowledgement-before-effects')
        self.completed('explicit-confirmation')

        self.control('fail-next-notification')
        status, _ = self.public('confirm', confirm, identity)
        self.require(status == codes['durableEffectPending'], 'durable-notification-admission')
        failed = self.control('snapshot')
        self.require(failed['available'] == reserved['available'] and failed['pendingNotifications'] == 1
                     and failed['notificationsSent'] == reserved['notificationsSent'], 'failed-effect-retains-ownership')
        self.restart()
        self.require(self.control('snapshot') == failed, 'retry-ownership-survives-restart')
        self.control('drain-notifications')
        drained = self.control('snapshot')
        self.require(drained['pendingNotifications'] == 0 and drained['notificationsSent'] == reserved['notificationsSent'] + 1
                     and drained['notificationAttempts'] == failed['notificationAttempts'] + 1
                     and drained['available'] == reserved['available'], 'single-notification-recovery')
        status, _ = self.public('confirm', confirm, identity)
        self.require(status == codes['replay'] and self.control('snapshot') == drained, 'confirmation-replay-no-duplicate-effect')
        self.completed('durable-notification-recovery')

        second_request = {**reserve, 'operationId': 'fixture-reserve-2'}
        status, second = self.public('reserve', second_request)
        self.require(status == codes['created'], 'second-reservation')
        status, _ = self.public('cancel', self.contract['cancel']['body'], second['reservationId'])
        self.require(status == 200, 'reservation-cancelled')
        cancelled = self.control('snapshot')
        status, _ = self.public('confirm', {**confirm, 'operationId': 'fixture-illegal-confirm'}, second['reservationId'])
        self.require(status == codes['conflictOrDenied'] and self.control('snapshot') == cancelled, 'illegal-transition-no-effects')
        self.completed('illegal-transition-no-effect')
        return {'schemaVersion': 1, 'status': 'passed', 'checks': self.checks,
                'exchanges': self.exchanges, 'restart': restart_evidence,
                'scope': 'HTTP/domain behavior only; architecture, public package adoption and browser acceptance are separate.'}
