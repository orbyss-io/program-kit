"""Explicit released-reference admission; never manufactures a live checkpoint.

Review preparation and admission start no agent. The admission acknowledges the
exact before-behavior and declared governance gaps, not historical approvals.
"""
from __future__ import annotations

import argparse
import shutil
import uuid
from pathlib import Path

from .common import LiveContractError, atomic_write_json, canonical_sha256, file_inventory, load_object, safe_relative, sha256_file, utc_now
from .evidence import EvidenceStore

KIND = 'released-reference-consumer'


def require(condition, message):
    if not condition:
        raise LiveContractError('LIVE_REFERENCE_' + message)


def binding(path: Path):
    return {'path': str(path.resolve()), 'sha256': sha256_file(path)}


def checked(reference):
    path = Path(reference['path'])
    require(path.is_file() and sha256_file(path) == reference['sha256'], 'EVIDENCE_CHANGED')
    return load_object(path)


def process_passed(process):
    return (process.get('exitCode') == 0 and process.get('cleanupComplete') is True
            and process.get('logsDrained') is True and not process.get('timedOut'))


def before_evidence(prepared: Path, browser: Path, extensions: Path, descriptor: Path):
    receipt = load_object(prepared / 'preparation.json')
    require(receipt.get('kind') == 'reference-preparation' and receipt.get('historicalLiveCheckpoint') is False,
            'PREPARATION_KIND')
    require(receipt['release'] == load_object(descriptor) and receipt['descriptorSha256'] == sha256_file(descriptor), 'RELEASE_PROVENANCE')
    require(receipt['consumerInventory'] == file_inventory(prepared / 'consumer'), 'CONSUMER_CHANGED')
    require(all(process_passed(item['process']) for item in receipt['installedSetup'] + receipt['operations']), 'PREPARATION_PROCESS_FAILED')
    names = {item['name'] for item in receipt['operations']}
    require({'renew', 'locked', 'build-dotnet', 'build-typescript', 'build-web'} <= names, 'PREPARATION_OPERATIONS_MISSING')
    http_path = prepared / 'evidence/http/http-acceptance.json'
    http, web, architecture = load_object(http_path), load_object(browser), load_object(extensions)
    inventory_hash = canonical_sha256(receipt['consumerInventory'])
    require(http.get('status') == 'passed' and http.get('consumerInventorySha256') == inventory_hash, 'HTTP_BEHAVIOR')
    expected_http = {'typed-v1-admission', 'policies-before-effects', 'idempotent-admission', 'durable-restart', 'explicit-confirmation', 'durable-notification-recovery', 'illegal-transition-no-effect'}
    require(expected_http <= {c.get('id') for c in http.get('checks', []) if c.get('status') == 'passed'}
            and len(http.get('hosts', [])) >= 3, 'RESTART_EVIDENCE_MISSING')
    require(all(p.get('cleanupComplete') and p.get('logsDrained') for p in http['hosts']), 'HOST_CLEANUP')
    supplements = (web, architecture) if web.get('kind') else (architecture,)
    if not web.get('kind'):
        require(web == receipt.get('browser') and process_passed(load_object(browser.parent / 'process/process.json')), 'BROWSER_PREPARATION_BINDING')
        web = {'kind': 'reference-browser-supplement', 'browser': web}
    for supplement in supplements:
        require(supplement.get('preparationSha256') == sha256_file(prepared / 'preparation.json')
                and supplement.get('consumerInventorySha256') == inventory_hash, 'SUPPLEMENT_STALE')
    require(web.get('kind') == 'reference-browser-supplement' and web.get('browser', {}).get('status') == 'passed', 'BROWSER_BEHAVIOR')
    checks = {(c.get('engine'), c.get('id')) for c in web['browser'].get('checks', []) if c.get('status') == 'passed'}
    require({(e, c) for e in ('chromium', 'webkit') for c in ('browser-reserve-acknowledge-confirm', 'accessible-validation')} <= checks,
            'BROWSER_COVERAGE')
    require(architecture.get('kind') == 'reference-extension-supplement' and architecture.get('status') == 'passed'
            and all(architecture.get('checks', {}).values()) and len(architecture.get('checks', {})) >= 2, 'EXTENSION_BEHAVIOR')
    require(architecture['resultsSha256'] == sha256_file(extensions.parent / 'results.xml'), 'EXTENSION_RESULTS_CHANGED')
    require(bool(architecture.get('compiledAssemblies')) and all(process_passed(item['process']) for item in architecture.get('operations', [])), 'COMPILED_PROOF_REQUIRED')
    return receipt, [binding(p) for p in (prepared / 'preparation.json', http_path, browser, extensions, descriptor)]


def prepare_review(prepared: Path, browser: Path, extensions: Path, root: Path, output: Path):
    fixture = root / 'tests/live/scenarios/knowledge-application/v1'
    receipt, evidence = before_evidence(prepared, browser, extensions, fixture / 'reference-source.json')
    identity = fixture / 'reference-identity'
    require(identity.is_dir(), 'IDENTITY_FIXTURE_MISSING')
    store = EvidenceStore(root / 'artifacts/live-acceptance/v2')
    store.initialize()
    files = receipt['consumerInventory'][:]
    for record in files:
        require(store.put_file(prepared / 'consumer' / safe_relative(record['path'])) == {k: record[k] for k in ('sha256', 'size')}, 'OBJECT_CHANGED')
    existing = {r['path'] for r in files}
    identity_files = file_inventory(identity)
    for record in identity_files:
        require(record['path'] not in existing, 'IDENTITY_OVERLAY_COLLISION')
        store.put_file(identity / safe_relative(record['path']))
        files.append(record)
    # Retain all before evidence alongside its manifest. Revalidate its source hashes
    # at admission; a review document is not an arbitrary passing evidence generator.
    report = {
        'schemaVersion': 1, 'kind': KIND + '-review', 'historicalLiveCheckpoint': False,
        'referenceId': 'reference-' + uuid.uuid4().hex, 'createdAt': utc_now(),
        'store': str(store.root), 'release': receipt['release'], 'evidence': evidence,
        'files': sorted(files, key=lambda item: item['path'].casefold()), 'identityFiles': identity_files,
        'beforeConsumerInventorySha256': canonical_sha256(receipt['consumerInventory']),
        'beforeEvidenceFiles': file_inventory(prepared / 'evidence'),
        'toolchain': receipt['toolchain'],
        'governance': {'status': 'declared-legacy-gaps', 'historicalApprovals': False,
            'expectedRemediation': ['specs/001-equipment-lending'],
            'rule': 'Existing implemented behavior is independently proven. The proposed canonical model and documented RM01 have no invented ratification, bootstrap approval or intake confirmation. Candidate continuation must surface and resolve these gaps through real human gates.'},
        'acceptanceScope': 'Released installation, native locks, independent HTTP/browser behavior and Core adapter replacement. Reference admission is not candidate phase acceptance or a matched token baseline.'}
    report['reviewSha256'] = canonical_sha256(report)
    require(not output.exists(), 'REVIEW_ALREADY_EXISTS')
    atomic_write_json(output, report)
    return report


def validate_review(path: Path):
    report = load_object(path)
    unsigned = dict(report)
    require(unsigned.pop('reviewSha256', None) == canonical_sha256(unsigned), 'REVIEW_SEAL_CHANGED')
    require(report.get('kind') == KIND + '-review' and report.get('historicalLiveCheckpoint') is False, 'REVIEW_KIND')
    evidence = [checked(ref) for ref in report['evidence']]
    fixture = Path(__file__).resolve().parents[3] / 'tests/live/scenarios/knowledge-application/v1'
    require(report['release'] == load_object(fixture / 'reference-source.json'), 'PINNED_RELEASE_CHANGED')
    require(report['identityFiles'] == file_inventory(fixture / 'reference-identity'), 'IDENTITY_FIXTURE_CHANGED')
    expected = sorted(evidence[0]['consumerInventory'] + report['identityFiles'], key=lambda item: item['path'].casefold())
    require(report['files'] == expected, 'REVIEW_INVENTORY_CHANGED')
    preparation = Path(report['evidence'][0]['path']).parent
    require(report.get('beforeEvidenceFiles') == file_inventory(preparation / 'evidence'), 'BEFORE_EVIDENCE_CHANGED')
    before_evidence(preparation, Path(report['evidence'][2]['path']), Path(report['evidence'][3]['path']), Path(report['evidence'][4]['path']))
    require(evidence[0]['release'] == report['release'], 'REVIEW_RELEASE_CHANGED')
    validate_objects(report)
    return report


def validate_objects(report):
    store = EvidenceStore(Path(report['store']))
    paths = set()
    for record in report['files']:
        relative = safe_relative(record['path']).as_posix()
        require(relative.casefold() not in paths, 'DUPLICATE_PATH')
        paths.add(relative.casefold())
        import re
        require(isinstance(record['sha256'], str) and re.fullmatch('[0-9a-f]{64}', record['sha256']), 'OBJECT_DIGEST_INVALID')
        source = store.objects / record['sha256']
        require(source.is_file() and sha256_file(source) == record['sha256'] and source.stat().st_size == record['size'], 'OBJECT_CHANGED')
    require(all(record in report['files'] for record in report['identityFiles']), 'IDENTITY_NOT_BOUND')


def admit(review: Path, output: Path, review_sha: str, answer: str, source: str):
    report = validate_review(review)
    require(report['reviewSha256'] == review_sha and answer == 'ADMIT ' + review_sha and bool(source.strip()), 'EXACT_HUMAN_ADMISSION_REQUIRED')
    require(not output.exists(), 'ADMISSION_ALREADY_EXISTS')
    result = {'schemaVersion': 1, 'kind': KIND, 'historicalLiveCheckpoint': False,
        'referenceId': report['referenceId'], 'review': binding(review), 'reviewSha256': review_sha,
        'confirmation': {'text': answer, 'source': source, 'confirmedAt': utc_now()}}
    atomic_write_json(output, result)
    return result


def validate_admission(path: Path):
    admission = load_object(path)
    require(admission.get('kind') == KIND and admission.get('historicalLiveCheckpoint') is False, 'ADMISSION_KIND')
    checked(admission['review'])
    review = validate_review(Path(admission['review']['path']))
    require(admission.get('reviewSha256') == review['reviewSha256'] and admission.get('referenceId') == review['referenceId'], 'ADMISSION_BINDING')
    confirmation = admission.get('confirmation', {})
    require(confirmation.get('text') == 'ADMIT ' + review['reviewSha256'] and bool(confirmation.get('source'))
            and bool(confirmation.get('confirmedAt')), 'EXACT_HUMAN_ADMISSION_REQUIRED')
    return admission, review


def materialize(path: Path, destination: Path):
    admission, review = validate_admission(path)
    require(not destination.exists(), 'DESTINATION_EXISTS')
    destination.mkdir(parents=True)
    store = EvidenceStore(Path(review['store']))
    for record in review['files']:
        target = destination / safe_relative(record['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(store.objects / record['sha256'], target)
    require(file_inventory(destination) == review['files'], 'COPY_INVENTORY_CHANGED')
    return admission, review


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    review = commands.add_parser('review')
    for name in ('prepared', 'browser', 'extensions', 'output'):
        review.add_argument('--' + name, type=Path, required=True)
    approve = commands.add_parser('admit')
    for name in ('review', 'output'):
        approve.add_argument('--' + name, type=Path, required=True)
    for name in ('review-sha256', 'confirmation-text', 'confirmation-source'):
        approve.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if args.command == 'review':
        result = prepare_review(args.prepared.resolve(), args.browser.resolve(), args.extensions.resolve(), Path(__file__).resolve().parents[3], args.output.resolve())
        print('Prepared reference review: ' + result['reviewSha256'] + '; no admission or paid authorization issued.')
    else:
        admit(args.review.resolve(), args.output.resolve(), args.review_sha256, args.confirmation_text, args.confirmation_source)
        print('Explicit reference admission recorded; no paid authorization issued.')
