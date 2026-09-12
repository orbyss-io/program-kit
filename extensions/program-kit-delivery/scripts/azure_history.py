"""Complete, bounded Azure observations. An unavailable stream never means no changes."""
from __future__ import annotations
from copy import deepcopy
from azure_provider import require
from azure_transport import AzureError
from delivery_contract import authority

PAGE = 200
MAX_PAGES = 1000


def offset_pages(api, path, *, version='7.1'):
    rows, seen = [], set()
    for _ in range(MAX_PAGES):
        result = api.call('GET', path, query={'$top': PAGE, '$skip': len(rows)}, version=version)
        batch = result.get('value') if isinstance(result, dict) else result
        require(isinstance(batch, list), 'history page is incomplete')
        if not batch:
            return rows
        for row in batch:
            identity = row.get('id', row.get('rev', row.get('version')))
            require(identity is not None and identity not in seen, 'history pagination repeated an identity')
            seen.add(identity)
        rows.extend(batch)
        # Request the next page even after a short page: providers may cap page size.
    raise AzureError('history pagination bound exceeded; observation incomplete')


def comments(provider, identity):
    path = f'/{provider.project}/_apis/wit/workItems/{identity}/comments'
    rows, tokens, identities, token = [], set(), set(), None
    for _ in range(MAX_PAGES):
        query = {'$top': PAGE, 'includeDeleted': 'true', 'order': 'asc'}
        if token:
            query['continuationToken'] = token
        result = provider.api.call('GET', path, query=query, version='7.1-preview.4')
        batch = result.get('comments')
        require(isinstance(batch, list), 'comment coverage incomplete')
        for comment in batch:
            require(comment['id'] not in identities, 'duplicate comment in paginated observation')
            identities.add(comment['id'])
            versions = provider.api.call('GET', path + f'/{comment["id"]}/versions', version='7.1-preview.1')
            versions = versions.get('value') if isinstance(versions, dict) else versions
            require(isinstance(versions, list), 'comment version coverage incomplete')
            observed = sorted(v['version'] for v in versions)
            require(observed == list(range(1, comment['version'] + 1)), 'comment version history has a gap')
            rows.append({'comment': comment, 'versions': versions})
        token = result.get('continuationToken')
        if not token:
            require(result.get('totalCount', len(rows)) == len(rows), 'comment total differs from observed coverage')
            return rows
        require(token not in tokens, 'repeated comment continuation token')
        tokens.add(token)
    raise AzureError('comment pagination bound exceeded; observation incomplete')


def stable(value):
    """Drop display/navigation and provider audit values, retain history identities and text."""
    if isinstance(value, list):
        return [stable(row) for row in value]
    if not isinstance(value, dict):
        return value
    omitted = {'_links', 'url', 'imageUrl', 'renderedText'}
    # Preserve relationship URLs: they are identity, not display navigation.
    if 'rel' in value:
        omitted.remove('url')
    return {key: stable(child) for key, child in value.items() if key not in omitted}


def fingerprint(snapshot):
    return authority.digest(stable(snapshot))


def read(provider, identity):
    coverage = {'item': False, 'updates': False, 'comments': False}
    try:
        first = provider.item(identity)
        coverage['item'] = True
    except AzureError as error:
        deletion = None
        if error.status in (404, 410):
            try:
                deletion = provider.api.call('GET', f'/{provider.project}/_apis/wit/recyclebin/{identity}')
                require(int(deletion['id']) == identity and deletion.get('deletedDate') and deletion.get('deletedBy'),
                        'deletion evidence incomplete')
            except (AzureError, KeyError, ValueError):
                deletion = None
        return {'id': identity, 'available': False, 'coverage': coverage,
                'status': 'deleted' if deletion else 'unknown', 'deletion': deletion, 'error': str(error)}
    try:
        path = f'/{provider.project}/_apis/wit/workItems/{identity}'
        updates = offset_pages(provider.api, path + '/updates')
        ids = [u['id'] for u in updates]
        require(ids == list(range(1, len(ids) + 1)) and ids, 'update history has a gap')
        coverage['updates'] = True
        comment_rows = comments(provider, identity)
        coverage['comments'] = True
        # No provider snapshot spans all endpoints. Verify both ends of our read window.
        last = provider.item(identity)
        end_updates = offset_pages(provider.api, path + '/updates')
        end_comments = comments(provider, identity)
        require(stable(first) == stable(last) and stable(updates) == stable(end_updates)
                and stable(comment_rows) == stable(end_comments), 'provider changed during observation; retry observation')
        return {'id': identity, 'available': True, 'coverage': coverage, 'status': 'observed',
                'inScope': provider.in_scope(last), 'item': last, 'updates': updates, 'comments': comment_rows}
    except (AzureError, KeyError, ValueError) as error:
        return {'id': identity, 'available': True, 'coverage': coverage, 'status': 'incomplete',
                'inScope': provider.in_scope(first), 'item': first, 'error': str(error)}


def complete(snapshot):
    coverage = snapshot.get('coverage', {})
    return snapshot.get('status') == 'observed' and all(coverage.get(stream) is True for stream in ('item', 'updates', 'comments'))


def require_current(provider, snapshots):
    for identity, expected in snapshots.items():
        current = read(provider, int(identity))
        require(complete(current) and fingerprint(current) == fingerprint(expected),
                'history/comments changed or became unavailable after review: ' + str(identity))


def snapshot(provider, identity):
    """Single provider seam for deterministic fakes and actual endpoint observations."""
    return provider.evidence(identity)


def compatible(before, after, added_relations=(), written_fields=()):
    """Permit only explained operation deltas; never hide comments or edit/revert history."""
    from azure_planning import business_fields, relation_keys
    if not complete(before) or not complete(after) or stable(before['comments']) != stable(after['comments']):
        return False
    old, new = before['updates'], after['updates']
    if stable(new[:len(old)]) != stable(old):
        return False
    allowed_links = set(added_relations)
    for update in new[len(old):]:
        fields = business_fields(update.get('fields', {}))
        if not set(fields).issubset(written_fields):
            return False
        for key, delta in fields.items():
            if stable(delta.get('newValue')) != stable(after['item']['fields'].get(key)):
                return False
        relations = update.get('relations', {})
        if relations.get('removed') or relations.get('updated'):
            return False
        if not set(relation_keys(relations.get('added', []))).issubset(allowed_links):
            return False
    return True
