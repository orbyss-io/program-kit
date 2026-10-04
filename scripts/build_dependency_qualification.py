"""Build a portable qualification asset from preserved generic check evidence.

This prepares evidence only. It neither changes the profile registry nor grants
consumer architecture, migration, compatibility, or publication approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks


def require(condition, detail):
    if not condition:
        raise ValueError('Incomplete dependency qualification: ' + detail)


def build(profile: Path, native: Path, browser: Path, availability: Path, host: Path) -> dict:
    selected = blocks.load_json(profile)
    available = blocks.load_json(availability)
    require({p['packageKey']: p['version'] for p in available['artifacts']} == selected['artifacts'], 'public artifact pins differ')
    receipt = blocks.load_json(native / 'qualification.json')
    require(set(receipt) == {'schemaVersion', 'status', 'catalog', 'source', 'scope', 'steps', 'artifacts', 'activationMatrix', 'compositionMatrix'},
            'unexpected generic report fields')
    require(receipt.get('status') == 'generic-integration-passed', 'generic integration did not pass')
    require(receipt.get('catalog', {}).get('sha256') == selected['catalogResolutionSha256'], 'native profile differs')
    native_files = {'locked-restore': 'locked-restore.log', 'consumer-build-pack': 'consumer-build-pack.log',
                    'publisher-descriptors': 'publisher-metadata.json', 'public-exporter-restore': 'public-exporter-restore.log',
                    'activation-export-matrix': 'activation-matrix.json', 'producer-version-rejection': 'producer-version-rejection.log'}
    require(len(receipt['steps']) == len(native_files) and {s['id'] for s in receipt['steps']} == set(native_files), 'native stages differ')
    for step in receipt['steps']:
        require(step['exitCode'] == 0 and blocks.raw_sha256(native / native_files[step['id']]) == step['evidenceSha256'], 'native stage evidence changed')
    for key, path in [('recipeSha256', ROOT / 'tests/validate_default_dependency_profile.py'),
                      ('lockSha256', ROOT / 'tests/fixtures/default-dependency-profile/packages.lock.json')]:
        require(receipt['source'][key] == hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest(), 'native recipe or lock changed')
    browser_stages = {}
    for stage in ('strict-graph', 'renew', 'locked', 'bundle', 'browser'):
        path = browser / 'evidence' / stage / 'process.json'
        value = blocks.load_json(path)
        require(value['exitCode'] == 0 and not value['timedOut'] and value['cleanupComplete'] and value['logsDrained'], 'browser stage did not finish')
        for stream in ('stdout', 'stderr'):
            source = blocks.repository_path(path.parent, value[stream]['path'])
            require(blocks.raw_sha256(source) == value[stream]['sha256'], 'browser stream changed')
        browser_stages[stage] = blocks.raw_sha256(path)
    browser_profile = blocks.load_json(browser / 'qualification-profile.json')
    require(browser_profile['catalogResolutionSha256'] == selected['catalogResolutionSha256'], 'browser profile differs')
    require(bool(browser_profile['packages']) and all(selected['artifacts'].get('npm:' + key) == pin
            for key, pin in browser_profile['packages'].items()), 'browser package pins differ')
    browser_result = blocks.load_json(browser / 'qualification-result.json')
    require(browser_result.get('satisfied') is True and {'chromium', 'webkit'} <= set(browser_result['engines']), 'browser engines incomplete')
    summary = {'stages': browser_stages, 'profile': browser_profile, 'engines': browser_result['engines']}
    host_result = blocks.load_json(host / 'qualification-result.json')
    require(host_result.get('satisfied') is True and host_result['inputs']['catalogResolutionSha256'] == selected['catalogResolutionSha256'], 'host profile differs')
    host_artifact = next(p for p in available['artifacts'] if p['packageKey'] == 'oci:ghcr.io/orbyss-io/foundation-host')
    require(host_result['inputs']['hostImage'] == host_artifact['reference'] and
            host_result['inputs']['foundationRelease'] == selected['families']['foundation']['releaseVersion'], 'host image or runtime pin differs')
    results = host / 'compatibility-results.xml'
    require(blocks.raw_sha256(results) == host_result['resultsSha256'], 'host results changed')
    cases = ET.parse(results).getroot()
    require(not cases.findall('.//failure') and not cases.findall('.//error') and len(cases.findall('testcase')) == 5 and
            sorted(case.get('classname') + '.' + case.get('name') for case in cases.findall('testcase')) == host_result['cases'], 'host cases incomplete')
    receipt['status'] = 'dependency-profile-qualified'
    receipt['steps'] += [
        {'id': 'published-forms-browser', 'exitCode': 0, 'evidenceSha256': blocks.canonical_sha256(summary)},
        {'id': 'public-artifact-availability', 'exitCode': 0, 'evidenceSha256': blocks.raw_sha256(availability)},
        {'id': 'published-host-runtime', 'exitCode': 0, 'evidenceSha256': blocks.canonical_sha256(host_result)}]
    receipt['browserIntegration'] = summary
    receipt['availableArtifacts'] = available['artifacts']
    receipt['hostRuntime'] = host_result
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('profile', 'native', 'browser', 'availability', 'host', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to(ROOT)
    result = build(args.profile, args.native, args.browser, args.availability, args.host)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print('Prepared qualification asset: ' + str(output) + '\nSHA-256: ' + blocks.raw_sha256(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
