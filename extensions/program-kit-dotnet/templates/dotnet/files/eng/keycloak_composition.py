"""Reconcile owned Development registrations through the pinned Keycloak API.

The full import creates a fresh realm. Later preparations update its declared
registrations in place; users, roles, sessions and database contents are preserved.
No response bodies, credentials or tokens become command/evidence output.
"""
from __future__ import annotations
from copy import deepcopy
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

import composition_model as model

OWNER = 'programKitCompositionOwner'


def owner(graph, authority):
    return graph['compositionId'] + '/' + authority


def stamp(graph, authority, realm):
    value = owner(graph, authority)
    realm.setdefault('attributes', {})[OWNER] = value
    for row in [*realm['clients'], *realm['clientScopes']]:
        row.setdefault('attributes', {})[OWNER] = value
    return realm


class Administration:
    def __init__(self, origin, password):
        uri = urlsplit(origin)
        # Docker publishes managed identity on IPv4 loopback. Connect to that
        # exact listener while retaining the declared Host/issuer; no DNS retry.
        self.origin = ('http://127.0.0.1:' + str(uri.port)) if uri.scheme == 'http' and uri.hostname == 'localhost' else origin
        self.host = uri.netloc
        self.token = None
        self.refresh = None
        self.expires = 0
        data = urlencode({'grant_type': 'password', 'client_id': 'admin-cli',
                          'username': '_programkit', 'password': password}).encode()
        response, _ = self.request('POST', '/realms/master/protocol/openid-connect/token', data,
                                   'application/x-www-form-urlencoded')
        model.require(isinstance(response, dict) and isinstance(response.get('access_token'), str),
                      'owned Keycloak administration authentication failed')
        self.token = response['access_token']
        self.refresh = response.get('refresh_token')
        self.expires = time.monotonic() + int(response['expires_in'])

    def request(self, method, path, payload=None, content_type='application/json'):
        if self.token and time.monotonic() >= self.expires - 10:
            model.require(self.refresh, 'owned identity administration session cannot be refreshed')
            self.token = None
            data = urlencode({'grant_type': 'refresh_token', 'client_id': 'admin-cli', 'refresh_token': self.refresh}).encode()
            response, _ = self.request('POST', '/realms/master/protocol/openid-connect/token', data,
                                       'application/x-www-form-urlencoded')
            self.token = response['access_token']; self.refresh = response.get('refresh_token')
            self.expires = time.monotonic() + int(response['expires_in'])
        headers = {'Content-Type': content_type, 'Host': self.host}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode() if payload is not None else None
        try:
            with urlopen(Request(self.origin + path, data=data, headers=headers, method=method), timeout=30) as response:
                raw = response.read(1_048_577)
                model.require(len(raw) <= 1_048_576, 'owned identity administration response exceeds its bounded size')
                return json.loads(raw) if raw else None, response.headers
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            status = error.code if isinstance(error, HTTPError) else 'transport'
            # Never retain a response, request payload or access token on failure.
            raise ValueError('PKC110 owned identity reconciliation failed: ' + method + ' status=' + str(status)) from None

    def get(self, path):
        return self.request('GET', path)[0]

    def upsert(self, base, desired, existing, identity):
        row = existing.get(desired[identity])
        payload = deepcopy(desired)
        if row:
            model.require(row.get('attributes', {}).get(OWNER) == desired['attributes'][OWNER],
                          'identity registration is not owned by this composition: ' + desired[identity])
            if not contains(row, payload):
                self.request('PUT', base + '/' + quote(row['id'], safe=''), payload)
            return row['id']
        _, headers = self.request('POST', base, payload)
        location = headers.get('Location', '')
        model.require(location, 'identity creation omitted its resource identity')
        return location.rsplit('/', 1)[-1]


def contains(actual, desired):
    """Compare declared fields; provider IDs/defaults do not trigger mutations."""
    if isinstance(desired, dict):
        return isinstance(actual, dict) and all(key in actual and contains(actual[key], value) for key, value in desired.items())
    if isinstance(desired, list):
        return isinstance(actual, list) and len(actual) == len(desired) and all(contains(a, d) for a, d in zip(actual, desired))
    return actual == desired


def reconcile(graph, authority, realm, password, previous=None):
    binding = model.environment(graph)[authority]
    model.require(binding['provider'] == 'keycloak' and binding['mode'] == 'managed',
                  'owned identity reconciliation requires its selected Keycloak binding')
    desired_owner = owner(graph, authority)
    admin = Administration(binding['publicOrigin'], password)
    base = '/admin/realms/' + quote(binding['realm'], safe='')
    current = admin.get(base)
    model.require(current.get('attributes', {}).get(OWNER) == desired_owner,
                  'existing realm is not owned by the selected composition; preserve it and resolve placement')
    count_before = admin.get(base + '/users/count')
    settings = {key: value for key, value in realm.items()
                if key not in {'users', 'clients', 'clientScopes', 'roles', 'groups', 'id'}}
    settings['attributes'] = {**current.get('attributes', {}), **settings.get('attributes', {})}
    if not contains(current, settings):
        admin.request('PUT', base, settings)

    scope_base = base + '/client-scopes'
    scopes = {row['name']: row for row in admin.get(scope_base)}
    scope_ids = {name: row['id'] for name, row in scopes.items()}
    for desired in realm['clientScopes']:
        payload = {key: value for key, value in desired.items() if key != 'protocolMappers'}
        scope_id = admin.upsert(scope_base, payload, scopes, 'name')
        scope_ids[desired['name']] = scope_id
        mapper_base = scope_base + '/' + quote(scope_id, safe='') + '/protocol-mappers/models'
        existing = {row['name']: row for row in admin.get(mapper_base)}
        wanted = {row['name']: row for row in desired.get('protocolMappers', [])}
        for name, row in wanted.items():
            if name in existing:
                if not contains(existing[name], row):
                    admin.request('PUT', mapper_base + '/' + quote(existing[name]['id'], safe=''), row)
            else:
                admin.request('POST', mapper_base, row)
        for name, row in existing.items():
            if name not in wanted:
                admin.request('DELETE', mapper_base + '/' + quote(row['id'], safe=''))

    client_base = base + '/clients'
    clients = {row['clientId']: row for row in admin.get(client_base)}
    identities = {}
    for desired in realm['clients']:
        payload = {key: value for key, value in desired.items() if key not in {'defaultClientScopes', 'optionalClientScopes'}}
        client_id = admin.upsert(client_base, payload, clients, 'clientId')
        identities[desired['clientId']] = client_id
        for key, endpoint in (('defaultClientScopes', 'default-client-scopes'), ('optionalClientScopes', 'optional-client-scopes')):
            path = client_base + '/' + quote(client_id, safe='') + '/' + endpoint
            actual = {row['name']: row['id'] for row in admin.get(path)}
            wanted = set(desired.get(key, []))
            model.require(wanted <= set(scope_ids), 'client refers to an unmaterialized identity scope')
            for name, scope_id in actual.items():
                if name not in wanted:
                    admin.request('DELETE', path + '/' + quote(scope_id, safe=''))
            for name in sorted(wanted - set(actual)):
                admin.request('PUT', path + '/' + quote(scope_ids[name], safe=''))
    # Retire only registrations previously recorded as this composition's own.
    # Disabling preserves identity records and user history without admitting grants.
    for name, identity in (previous or {}).get('clients', {}).items():
        if name in identities:
            model.require(identities[name] == identity, 'owned client identity was replaced outside composition reconciliation')
        elif name in clients:
            row = clients[name]
            model.require(row['id'] == identity and row.get('attributes', {}).get(OWNER) == desired_owner,
                          'retired identity registration ownership changed')
            admin.request('PUT', client_base + '/' + quote(identity, safe=''), {'enabled': False})
    model.require(admin.get(base + '/users/count') == count_before, 'owned identity reconciliation changed user cardinality')
    return {'status': 'reconciled', 'realm': binding['realm'], 'clients': identities,
            'userCountPreserved': True, 'users': count_before}
