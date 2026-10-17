"""Read-only, bounded maintenance-packet inspection; never a publisher attestation.

This is evidence tooling, not production credential scanning. It checks exact
UTF-8 packet inventories and known fixture credentials, complete private-key PEM
markers, token-like text and personal paths. It never builds or shares a packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

PRIVATE_PEM = re.compile(r'-----BEGIN (?:[A-Z0-9][A-Z0-9 -]* )?PRIVATE KEY-----', re.I)
TOKEN = re.compile(r'eyJ[A-Za-z0-9_-]{30,}')
PERSONAL_PATH = re.compile(r'(?:[a-z]:[\\/]+users[\\/]+|/(?:users|home)/)\w[\w .-]*[\\/]', re.I)
MAX_TEXT_BYTES = 10 * 1024 * 1024
MAX_PACKET_BYTES = 100 * 1024 * 1024


def known_credentials(identity):
    """Collect actual values from a supplied Keycloak fixture; print none of them."""
    if not isinstance(identity, dict):
        raise ValueError('Identity fixture must be a JSON object')
    users, clients = identity.get('users', []), identity.get('clients', [])
    if not isinstance(users, list) or not isinstance(clients, list) or any(not isinstance(item, dict) for item in [*users, *clients]):
        raise ValueError('Unsupported identity fixture collections')
    values = []
    for user in users:
        credentials = user.get('credentials', [])
        if not isinstance(credentials, list) or any(not isinstance(item, dict) for item in credentials):
            raise ValueError('Unsupported identity fixture credentials')
        values.extend(item.get('value') for item in credentials)
    values += [client.get('secret') for client in clients]
    if any(value is not None and not isinstance(value, str) for value in values):
        raise ValueError('Known fixture credential values must be strings')
    return {value for value in values if isinstance(value, str) and value}


def inspect_text(text, credentials=(), personal_roots=()):
    findings = []
    for kind, pattern in (('private-key-pem', PRIVATE_PEM), ('token-like-text', TOKEN), ('personal-path', PERSONAL_PATH)):
        count = len(pattern.findall(text))
        if count:
            findings.append({'kind': kind, 'count': count})
    count = sum(1 for value in set(credentials) if value and value in text)
    if count:
        findings.append({'kind': 'known-fixture-credential', 'count': count})
    normalized = text.replace('\\\\', '\\').replace('\\', '/').casefold()
    roots = {str(value).replace('\\', '/').casefold().rstrip('/') for value in personal_roots if value}
    if any(root in normalized for root in roots):
        findings.append({'kind': 'known-personal-root', 'count': 1})
    return findings


def _contained(root, relative):
    path = PurePosixPath(relative)
    if (not isinstance(relative, str) or str(path) != relative or path.is_absolute()
            or '..' in path.parts or '\\' in relative or ':' in relative or relative == 'manifest.json'):
        raise ValueError('Unsafe or aliased maintenance packet path')
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Maintenance packet path escapes selected root')
    for entry in (target, *[parent for parent in target.parents if parent != root and parent.is_relative_to(root)]):
        if entry.is_symlink() or getattr(entry, 'is_junction', lambda: False)():
            raise ValueError('Linked maintenance packet inputs are unsupported')
    return target


def inspect_packet(directory, *, credentials=(), personal_roots=(), expected_manifest=None):
    root = Path(directory).resolve(strict=True)
    manifest_path = root / 'manifest.json'
    if manifest_path.is_symlink() or getattr(manifest_path, 'is_junction', lambda: False)():
        raise ValueError('Linked packet manifest is unsupported')
    with manifest_path.open('rb') as stream:
        raw = stream.read(MAX_TEXT_BYTES + 1)
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError('Packet manifest exceeds the bounded text budget')
    identity = hashlib.sha256(raw).hexdigest()
    if expected_manifest is not None and identity != expected_manifest:
        raise ValueError('Packet manifest differs from the supplied historical identity; preserve both records')
    manifest = json.loads(raw.decode('utf-8-sig'))
    rows = manifest.get('files')
    if not isinstance(rows, list) or not rows or len(rows) > 10000:
        raise ValueError('A bounded nonempty exact file inventory is required')
    selected = {}
    folded = set()
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('path'), str)
                or type(row.get('bytes')) is not int or row['bytes'] < 0 or row['bytes'] > MAX_TEXT_BYTES
                or not isinstance(row.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', row['sha256'])):
            raise ValueError('Unsupported maintenance packet inventory row')
        name = row['path']
        if name.casefold() in folded:
            raise ValueError('Duplicate or case-aliased maintenance packet path')
        folded.add(name.casefold())
        selected[name] = (_contained(root, name), row)
    if sum(row['bytes'] for _, row in selected.values()) > MAX_PACKET_BYTES:
        raise ValueError('Packet exceeds the bounded total text budget')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Linked maintenance packet inputs are unsupported')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(selected) | {'manifest.json'}:
        raise ValueError('Packet inventory has missing or unlisted inputs')
    findings = [{'path': 'manifest.json', **finding} for finding in inspect_text(raw.decode('utf-8-sig'), credentials, personal_roots)]
    for name, (path, row) in selected.items():
        name_findings = inspect_text(name, credentials, personal_roots)
        label = '<sensitive-name>' if name_findings else name
        findings.extend({'path': label, 'pathSha256': hashlib.sha256(name.encode()).hexdigest(), **finding} for finding in name_findings)
        with path.open('rb') as stream:
            data = stream.read(MAX_TEXT_BYTES + 1)
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Packet bytes differ from their inventory: ' + label)
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise ValueError('Opaque/non-UTF-8 packet input needs separate inspection: ' + label) from error
        findings.extend({'path': label, **finding} for finding in inspect_text(text, credentials, personal_roots))
    return {'kind': 'maintenance-packet-inspection', 'manifestSha256': identity,
            'matchesSuppliedManifest': None if expected_manifest is None else True,
            'files': len(selected), 'manifestInspected': True, 'knownCredentialValues': len(set(credentials)),
            'satisfied': not findings, 'findings': findings,
            'scope': 'Exact UTF-8 inventory and bounded supplied-credential/pattern checks; no publisher authentication, production-secret-scan or sharing claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--identity-fixture', type=Path)
    parser.add_argument('--personal-root', action='append', default=[])
    parser.add_argument('--expected-manifest-sha256')
    args = parser.parse_args()
    try:
        credentials = known_credentials(json.loads(args.identity_fixture.read_text(encoding='utf-8-sig'))) if args.identity_fixture else set()
        result = inspect_packet(args.packet, credentials=credentials, personal_roots=args.personal_root,
                                expected_manifest=args.expected_manifest_sha256)
        print(json.dumps(result))
        return 0 if result['satisfied'] else 1
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({'kind': 'maintenance-packet-inspection', 'satisfied': False, 'diagnostic': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
