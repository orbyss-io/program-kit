"""Azure planning observations and conditional operational storage."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import re

from azure_transport import AzureError
from azure_setup import actor
from delivery_contract import authority

GIT_SECURITY = '2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87'
UUID = re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')


def require(value, message):
    if not value:
        raise AzureError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def literal(value):
    return "'" + value.replace("'", "''") + "'"


class AzureProvider:
    def __init__(self, api, profile):
        self.api, self.profile = api, profile
        self.settings = profile['azure']
        require(api.organization == self.settings['organization'], 'organization/profile mismatch')
        self.project = self.settings['projectId']
        require(UUID.fullmatch(self.project), 'immutable Azure project ID required')
        self.coord = profile['coordination']
        require(UUID.fullmatch(self.coord['repositoryId']), 'immutable coordination repository ID required')
        self.prefix = f'/{self.project}/_apis/git/repositories/{self.coord["repositoryId"]}'
        branch = self.coord['branch']
        require(re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*', branch), 'invalid coordination branch')
        self.state_path = self.coord['statePath']
        require(self.state_path and all(p not in ('', '.', '..') for p in self.state_path.split('/'))
                and not any(c in self.state_path for c in '\\:%?#'), 'invalid state path')

    def identities(self):
        identities = sorted(set(identity for people in self.profile['roles'].values() for identity in people))
        require(identities and all(UUID.fullmatch(i) for i in identities), 'roles must name verified individual Azure identity IDs')
        result = self.api.call('GET', '/_apis/identities', graph=True, version='7.1-preview.1',
                               query={'identityIds': ','.join(identities), 'queryMembership': 'None'})['value']
        by_id = {entry['id']: entry for entry in result}
        require(set(by_id) == set(identities), 'one or more role identities are unavailable')
        for entry in result:
            require(entry.get('isActive') is True and entry.get('isContainer') is not True
                    and entry.get('properties', {}).get('SchemaClassName', {}).get('$value') == 'User'
                    and entry.get('descriptor'), 'inactive or group identity is unsupported')
        return by_id

    def authorize(self, role):
        who = actor(self.api)
        identities = self.identities()
        require(who['id'] in self.profile['roles'][role], 'authenticated person lacks configured ' + role + ' authority')
        require(identities[who['id']]['descriptor'] == who['descriptor'], 'authenticated identity descriptor mismatch')
        return who

    def assignment_value(self, identity):
        person = self.identities().get(identity)
        require(person is not None, 'assignment identity is not configured')
        account = person.get('properties', {}).get('Account', {}).get('$value')
        require(isinstance(account, str) and bool(account), 'assignment account unavailable')
        return account

    def areas(self):
        tree = self.api.call('GET', f'/{self.project}/_apis/wit/classificationnodes/areas', query={'$depth': 14})
        result = {}
        def visit(node, path):
            require(not node.get('hasChildren') or bool(node.get('children')), 'area observation incomplete')
            result[node['identifier']] = path
            for child in node.get('children', []):
                visit(child, path + '\\' + child['name'])
        visit(tree, tree['name'])
        for root in self.settings['areaRoots']:
            require(result.get(root['id']) == root['path'], 'selected area moved, renamed or unavailable; review scope')
        return result

    def discover_capabilities(self):
        project = self.api.call('GET', '/_apis/projects/' + self.project, query={'includeCapabilities': 'true'})
        repo = self.api.call('GET', self.prefix)
        require(project['id'] == self.project and repo['project']['id'] == self.project, 'project/repository mismatch')
        self.areas()
        identities = self.identities()
        result = {}
        for kind, native in self.profile['workTypes'].items():
            path = f'/{self.project}/_apis/wit/workitemtypes/{native}'
            fields = self.api.list(path + '/fields', query={'$expand': 'all'})
            states = self.api.list(path + '/states')
            fields_by_name = {f['referenceName']: f for f in fields}
            mapping = self.settings['types'][kind]
            for canonical, native_field in mapping['fields'].items():
                require(native_field in fields_by_name, f'{kind}: mapped field {native_field} is unavailable')
            require(mapping['initialState'] in {s['name'] for s in states}, kind + ': initial state unavailable')
            result[kind] = {'fields': fields, 'states': states}
        return {'projectId': project['id'], 'process': project.get('capabilities', {}).get('processTemplate'),
                'types': result, 'identities': {i: {'id': i, 'descriptor': u['descriptor']} for i, u in identities.items()},
                'observedAt': utc()}

    def item(self, identity):
        require(isinstance(identity, int) and identity > 0, 'positive native work-item ID required')
        result = self.api.call('GET', f'/{self.project}/_apis/wit/workitems/{identity}', query={'$expand': 'relations'})
        require(result['fields']['System.TeamProject'] == self.project_name(), 'work item belongs to another project')
        return result

    def project_name(self):
        if not hasattr(self, '_project_name'):
            self._project_name = self.api.call('GET', '/_apis/projects/' + self.project)['name']
        return self._project_name

    def in_scope(self, item):
        path = item['fields'].get('System.AreaPath', '')
        return any(path == root['path'] or root['includeDescendants'] and path.startswith(root['path'] + '\\')
                   for root in self.settings['areaRoots'])

    def discover_epics(self):
        self.areas()
        clauses = ['[System.AreaPath] ' + ('UNDER ' if r['includeDescendants'] else '= ') + literal(r['path'])
                   for r in self.settings['areaRoots']]
        cursor, records, asof = 0, [], None
        while True:
            query = ('SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = ' + literal(self.project_name())
                + ' AND [System.WorkItemType] = ' + literal(self.profile['workTypes']['epic'])
                + ' AND (' + ' OR '.join(clauses) + ') AND [System.Id] > ' + str(cursor)
                + ' ORDER BY [System.Id] ASC' + (' ASOF ' + literal(asof) if asof else ''))
            page = self.api.call('POST', f'/{self.project}/_apis/wit/wiql', {'query': query}, query={'$top': 200})
            asof = asof or page['asOf']
            ids = [x['id'] for x in page['workItems']]
            require(ids == sorted(set(ids)) and all(i > cursor for i in ids), 'invalid discovery cursor')
            if not ids:
                break
            # Each current item is rechecked against scope; the query snapshot is discovery, not admission.
            records.extend(self.item(i) for i in ids)
            cursor = ids[-1]
            if len(ids) < 200:
                break
        return {'observedAt': utc(), 'queryAsOf': asof, 'complete': True,
                'items': [{'item': item, 'inScope': self.in_scope(item)} for item in records]}

    def head(self):
        refs = self.api.list(self.prefix + '/refs', query={'filter': 'heads/' + self.coord['branch']})
        matches = [r['objectId'] for r in refs if r['name'] == 'refs/heads/' + self.coord['branch']]
        require(len(matches) == 1, 'coordination branch missing or ambiguous')
        return matches[0]

    def find_operation(self, operation_id):
        # Whole-project scan: a moved item must not disappear from create recovery.
        # IDs partition the query so an empty/truncated single page never proves absence.
        cursor, matches = 0, []
        while True:
            page = self.api.call('POST', f'/{self.project}/_apis/wit/wiql', {'query':
                'SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = ' + literal(self.project_name())
                + ' AND [System.Id] > ' + str(cursor) + ' ORDER BY [System.Id] ASC'}, query={'$top': 200})
            ids = [x['id'] for x in page['workItems']]
            require(ids == sorted(set(ids)) and all(i > cursor for i in ids), 'incomplete recovery cursor')
            for identity in ids:
                item = self.item(identity)
                if any('Program Kit operation: ' + operation_id in value for value in item['fields'].values() if isinstance(value, str)):
                    matches.append(identity)
            if len(ids) < 200:
                return matches
            cursor = ids[-1]

    def file(self, commit, path, repository=None):
        require(re.fullmatch('[0-9a-f]{40}', commit), 'immutable commit required')
        prefix = self.prefix if repository is None else f'/{self.project}/_apis/git/repositories/{repository}'
        result = self.api.call('GET', prefix + '/items', query={'path': '/' + path, 'includeContent': 'true',
            'versionDescriptor.versionType': 'commit', 'versionDescriptor.version': commit})
        return result['content']

    def read(self):
        head = self.head()
        state = json.loads(self.file(head, self.state_path))
        require(state.get('schemaVersion') == 1 and state.get('space') == self.profile['space'], 'coordination state identity mismatch')
        return head, state

    def commit(self, expected, state, *, initial=False, extra_files=None):
        require(state['space'] == self.profile['space'], 'cannot write another delivery space')
        changes = [{'changeType': 'add' if initial else 'edit', 'item': {'path': '/' + self.state_path},
                    'newContent': {'content': json.dumps(state, sort_keys=True, indent=2) + '\n', 'contentType': 'rawtext'}}]
        for path, content in (extra_files or {}).items():
            require(path != self.state_path and all(s not in ('', '.', '..') for s in path.split('/')), 'invalid extra artifact path')
            changes.append({'changeType': 'add', 'item': {'path': '/' + path},
                            'newContent': {'content': content, 'contentType': 'rawtext'}})
        result = self.api.call('POST', self.prefix + '/pushes', {
            'refUpdates': [{'name': 'refs/heads/' + self.coord['branch'], 'oldObjectId': expected}],
            'commits': [{'comment': 'Program Kit delivery operation', 'changes': changes}]})
        return result['commits'][0]['commitId']

    def security_token(self):
        encoded = '/'.join(segment.encode('utf-16-le').hex() for segment in self.coord['branch'].split('/'))
        return f'repoV2/{self.project}/{self.coord["repositoryId"]}/refs/heads/{encoded}/'

    def protection_plan(self):
        identities = self.identities()
        namespaces = self.api.list('/_apis/securitynamespaces/' + GIT_SECURITY)
        actions = {action['name']: action['bit'] for ns in namespaces for action in ns['actions']}
        required = ('GenericRead', 'GenericContribute', 'ForcePush', 'ManagePermissions', 'EditPolicies')
        require(all(name in actions for name in required), 'Git permission definitions unavailable')
        deny = actions['ForcePush'] | actions['ManagePermissions'] | actions['EditPolicies']
        allow = actions['GenericRead'] | actions['GenericContribute']
        return {'token': self.security_token(), 'merge': False, 'accessControlEntries': [
            {'descriptor': identity['descriptor'], 'allow': allow, 'deny': deny} for identity in identities.values()]}

    def verify_protection(self):
        plan = self.protection_plan()
        acls = self.api.list('/_apis/accesscontrollists/' + GIT_SECURITY,
            query={'token': plan['token'], 'includeExtendedInfo': 'true', 'recurse': 'false'})
        acl = next((a for a in acls if a['token'].rstrip('/') == plan['token'].rstrip('/')), {})
        actual = acl.get('acesDictionary', {})
        for expected in plan['accessControlEntries']:
            entry = actual.get(expected['descriptor'], {})
            require(entry.get('deny', 0) & expected['deny'] == expected['deny'], 'coordination branch lacks explicit history/protection denies')
            require(entry.get('allow', 0) & expected['allow'] == expected['allow'], 'coordination branch lacks contribution permission')
            require(not entry.get('allow', 0) & expected['deny'], 'coordination branch retains conflicting creator grants')
        allowed = plan['accessControlEntries'][0]['allow']
        denied = plan['accessControlEntries'][0]['deny']
        for mask, expected in ((allowed, True), *((1 << i, False) for i in range(32) if denied & (1 << i))):
            result = self.api.call('GET', f'/_apis/permissions/{GIT_SECURITY}/{mask}',
                query={'tokens': plan['token'], 'alwaysAllowAdministrators': 'false'})
            values = result.get('value') if isinstance(result, dict) else result
            require(values == [expected], 'effective coordination permission differs from the required boundary')
        # ACL evidence is a cooperation boundary; administrators can change these rules.
        return {'token': plan['token'], 'aclDigest': authority.digest(acl), 'checkedAt': utc(),
                'administratorOverridePossible': True}

    def protect(self, reviewed_plan):
        require(reviewed_plan == self.protection_plan(), 'protection plan changed; review again')
        self.api.call('POST', '/_apis/accesscontrolentries/' + GIT_SECURITY, reviewed_plan)
        return self.verify_protection()

    def create(self, kind, fields, relations, *, validate_only=False):
        patch = [{'op': 'add', 'path': '/fields/' + key, 'value': value} for key, value in fields.items()]
        patch += [{'op': 'add', 'path': '/relations/-', 'value': value} for value in relations]
        return self.api.call('POST', f'/{self.project}/_apis/wit/workitems/${self.profile["workTypes"][kind]}', patch,
            patch=True, query={'validateOnly': str(validate_only).lower(), 'bypassRules': 'false'})

    def update(self, identity, revision, fields, relations=()):
        patch = [{'op': 'test', 'path': '/rev', 'value': revision}]
        patch += [{'op': 'add', 'path': '/fields/' + key, 'value': value} for key, value in fields.items()]
        patch += [{'op': 'add', 'path': '/relations/-', 'value': value} for value in relations]
        return self.api.call('PATCH', f'/{self.project}/_apis/wit/workitems/{identity}', patch, patch=True,
                             query={'bypassRules': 'false'})
