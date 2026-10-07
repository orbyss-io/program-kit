"""Scoped reviewed decisions inside plan.md; approved bootstrap history is read-only."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import os
import tempfile
from pathlib import Path
from feature_context import feature_scope

MARKER = r'(?m)^<!-- program-kit:plan-decisions ([^\r\n]*?) -->[ \t]*$'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def rows(root, feature):
    entry = feature_scope(root, feature)['entry']
    ledger = read(root / 'docs/architecture/bootstrap-prerequisites.json', {})
    candidates = [i for i in ledger.get('prerequisites', []) if i.get('disposition') == 'feature'
                  and i.get('trigger') == 'feature-plan' and i.get('verification', 'decision') == 'decision'
                  and i.get('status') != 'closed']
    if candidates and entry is None:
        raise ValueError('Resolve feature roadmap identity before applying retained feature-plan decisions')
    return [i for i in candidates if entry in i.get('affected_slices', [])]


def section(root, feature, reference):
    relative, separator, heading = reference.partition('#')
    if not separator or not heading.strip():
        raise ValueError('Decision evidence needs a normal artifact and exact heading: path#Heading')
    path = (root / relative).resolve()
    if not path.is_relative_to(feature.resolve()) or path.suffix != '.md':
        raise ValueError('Decision evidence must stay in the current feature Markdown artifacts')
    content = re.sub(MARKER, '', path.read_text(encoding='utf-8'), flags=re.S)
    matches = list(re.finditer(r'^(#{1,6}) ' + re.escape(heading) + r'\s*$', content, re.M))
    if len(matches) != 1:
        raise ValueError('Missing/ambiguous decision evidence section: ' + reference)
    match = matches[0]
    tail = content[match.end():]
    end = re.search(r'^#{1,' + str(len(match[1])) + r'} ', tail, re.M)
    value = tail[:end.start() if end else len(tail)].strip()
    if not value:
        raise ValueError('Decision evidence section is empty: ' + reference)
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def conditions(root, item):
    """Bind the retained condition and only its source inventory, never rewrite it."""
    from bootstrap_lifecycle import source_digest
    ledger = read(root / 'docs/architecture/bootstrap-prerequisites.json', {})
    sources = [s for s in ledger.get('sources', []) if item['id'] in s.get('prerequisites', [])]
    for source in sources:
        path = (root / source['path']).resolve()
        if not path.is_relative_to(root.resolve()) or source_digest(path) != source['sha256']:
            raise ValueError('Retained decision condition changed: ' + source['path'])
    return digest({'condition': item, 'sources': sources})


def saved(feature):
    path = feature / 'plan.md'
    content = path.read_text(encoding='utf-8') if path.is_file() else ''
    matches = re.findall(MARKER, content, re.S)
    if len(matches) > 1:
        raise ValueError('Duplicate plan decision record')
    value = json.loads(matches[0]) if matches else {'schemaVersion': 1, 'resolutions': []}
    if not isinstance(value, dict) or value.get('schemaVersion') != 1 or not isinstance(value.get('resolutions'), list):
        raise ValueError('Unsupported plan decision record')
    fields = {'prerequisite', 'entry', 'owner', 'briefSha256', 'conditionSha256', 'evidence',
              'evidenceSha256', 'reviewer', 'provenance'}
    if any(not isinstance(r, dict) or set(r) != fields or
           not all(isinstance(v, str) and v.strip() for v in r.values()) for r in value['resolutions']):
        raise ValueError('Malformed reviewed prerequisite resolution')
    ids = [r.get('prerequisite') for r in value['resolutions']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate prerequisite resolution')
    return value


def project(root, feature):
    scope = feature_scope(root, feature)
    items = rows(root, feature)
    records = {r['prerequisite']: r for r in saved(feature)['resolutions']}
    confirmed_hash = None
    if records:
        from specification_intake import check_spec
        try:
            confirmed_hash = check_spec(root, feature / 'spec.md')['briefHash']
        except (ValueError, OSError):
            pass
    unknown = set(records) - {i['id'] for i in items}
    # A later authoritative ledger closure legitimately makes a local row historical.
    closed_ids = {i['id'] for i in read(root / 'docs/architecture/bootstrap-prerequisites.json', {}).get('prerequisites', [])
                  if i.get('status') == 'closed'}
    if unknown - closed_ids:
        raise ValueError('Unknown or out-of-scope prerequisite resolution: ' + ', '.join(sorted(unknown - closed_ids)))
    result = []
    for item in items:
        row = records.get(item['id'])
        current = False
        diagnostic = 'Record the actual reviewed resolution in plan.md after normal design review.'
        if row:
            try:
                current = (confirmed_hash and row.get('entry') == scope['entry'] and row.get('owner') == item['owner']
                           and row.get('briefSha256') == confirmed_hash
                           and row.get('conditionSha256') == conditions(root, item)
                           and row.get('reviewer', '').strip() and row.get('provenance', '').strip()
                           and row.get('evidenceSha256') == section(root, feature, row['evidence']))
            except (ValueError, OSError, KeyError):
                current = False
            diagnostic = '' if current else 'Reviewed resolution is stale or incomplete; review only this decision and its changed inputs.'
        result.append({'id': item['id'], 'owner': item['owner'], 'task': item['task'],
                       'status': 'resolved' if current else 'pending-review', 'diagnostic': diagnostic})
    return result


def satisfied(root, entry, items):
    from specification_intake import spec_entries
    features = [p.parent for p in (root / 'specs').glob('*/spec.md')
                if entry in spec_entries(p.read_text(encoding='utf-8'))]
    if len(features) != 1:
        return set()
    allowed = {i['id'] for i in items if i.get('disposition') == 'feature' and i.get('trigger') == 'feature-plan'}
    return {r['id'] for r in project(root, features[0]) if r['status'] == 'resolved' and r['id'] in allowed}


def require_resolved(root, feature):
    pending = [r for r in project(root, feature) if r['status'] != 'resolved']
    if pending:
        raise ValueError('Resolve reviewed feature-plan decisions before dependent implementation: '
                         + '; '.join(r['id'] + ' (' + r['owner'] + '): ' + r['diagnostic'] for r in pending))


def record(root, feature, identity, reference, reviewer, provenance):
    """Persist a supplied normal review, not manufacture human approval or test evidence."""
    from specification_intake import check_spec
    confirmation = check_spec(root, feature / 'spec.md')
    matches = [i for i in rows(root, feature) if i['id'] == identity]
    if len(matches) != 1:
        raise ValueError('Select an open feature-plan decision for this exact slice; compatibility/delivery cannot be closed by a plan')
    if not reviewer.strip() or not provenance.strip() or '-->' in reviewer + provenance:
        raise ValueError('Name the actual reviewer and review provenance')
    item = matches[0]
    scope = feature_scope(root, feature)
    resolution = {'prerequisite': identity, 'entry': scope['entry'], 'owner': item['owner'],
                  'briefSha256': confirmation['briefHash'], 'conditionSha256': conditions(root, item),
                  'evidence': reference, 'evidenceSha256': section(root, feature, reference),
                  'reviewer': reviewer, 'provenance': provenance}
    value = saved(feature)
    value['resolutions'] = sorted([r for r in value['resolutions'] if r['prerequisite'] != identity]
                                 + [resolution], key=lambda r: r['prerequisite'])
    plan = feature / 'plan.md'
    content = re.sub(MARKER, '', plan.read_text(encoding='utf-8'), flags=re.S).rstrip()
    descriptor, temporary = tempfile.mkstemp(prefix='.plan-decisions-', suffix='.tmp', dir=plan.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content + '\n\n<!-- program-kit:plan-decisions '
                         + json.dumps(value, separators=(',', ':')) + ' -->\n')
        os.replace(temporary, plan)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return project(root, feature)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['project', 'record'])
    parser.add_argument('--repository', default='.')
    parser.add_argument('--feature-dir', required=True)
    parser.add_argument('--prerequisite')
    parser.add_argument('--evidence', help='Repository-relative normal Markdown artifact#Exact heading')
    parser.add_argument('--reviewer')
    parser.add_argument('--provenance', help='Actual normal-review context; never a fabricated human approval')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    feature = (root / args.feature_dir).resolve()
    try:
        os.chdir(root)
        if not feature.is_relative_to(root):
            raise ValueError('Feature escapes repository')
        if args.command == 'record' and not all([args.prerequisite, args.evidence, args.reviewer, args.provenance]):
            raise ValueError('Recording needs prerequisite, evidence, reviewer and provenance')
        value = project(root, feature) if args.command == 'project' else record(
            root, feature, args.prerequisite, args.evidence, args.reviewer, args.provenance)
        print(json.dumps(value))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
