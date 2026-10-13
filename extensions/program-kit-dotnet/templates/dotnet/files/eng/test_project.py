"""Preview/create a new consumer-owned test project from reviewed responsibilities.

Does not author behavioral tests, overwrite an existing project, or change selected pins.
Restore/lock generation and actual test execution remain separate required checks.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from central_packages import central_package_versions
from repository_architecture import inside, read, require, test_compile_contracts, validate_manifest


def scaffold(project, pins):
    contracts = test_compile_contracts(project, required=True)
    packages = sorted(set(project.get('packageReferences', [])) | contracts)
    require('xunit.v3.mtp-v2' in packages, 'PKA020 supported test scaffold requires selected xunit.v3.mtp-v2; other runners need an explicit consumer scaffold')
    for package in packages:
        require(package.casefold() in pins, 'PKA020 missing selected central pin: ' + project['path'] + ' / ' + package)
    document = ET.Element('Project', Sdk='Microsoft.NET.Sdk')
    properties = ET.SubElement(document, 'PropertyGroup')
    for name, value in {'OutputType': 'Exe', 'IsTestProject': 'true', 'IsPackable': 'false',
                        'UseMicrosoftTestingPlatformRunner': 'true'}.items():
        ET.SubElement(properties, name).text = value
    items = ET.SubElement(document, 'ItemGroup')
    for package in packages:
        attributes = {'Include': package}
        if package in contracts or package.startswith('CShells.'):
            attributes['PrivateAssets'] = 'all'
        ET.SubElement(items, 'PackageReference', attributes)
    if 'CShells.AspNetCore.Abstractions' in contracts:
        ET.SubElement(items, 'FrameworkReference', Include='Microsoft.AspNetCore.App')
    for reference in project.get('projectReferences', []):
        ET.SubElement(items, 'ProjectReference', Include=os.path.relpath(reference, Path(project['path']).parent).replace('\\', '/'))
    ET.indent(document, space='  ')
    return ET.tostring(document, encoding='utf-8') + b'\n'


def preview(root, relative):
    manifest = read(root / 'eng/architecture.json')
    proposal = copy.deepcopy(manifest)
    selected = [p for p in proposal['runtimeComposition']['projects'] if p['path'] == relative]
    require(len(selected) == 1 and selected[0]['role'] == 'test', 'PKA020 select one declared test owner in eng/architecture.json')
    project = selected[0]
    require(not inside(root, relative).exists(), 'PKA020 existing test project is consumer-owned; preserve it and review missing direct references')
    contracts = test_compile_contracts(project, required=True)
    project['packageReferences'] = sorted(set(project.get('packageReferences', [])) | contracts)
    validate_manifest(root, proposal)
    pins = central_package_versions(root)
    payload = scaffold(project, pins)
    changes = {relative: payload.decode(), 'eng/architecture.json': json.dumps(proposal, indent=2) + '\n'}
    basis = {'architectureSha256': hashlib.sha256((root / 'eng/architecture.json').read_bytes()).hexdigest(),
             'centralPins': pins, 'projectAbsent': relative}
    digest = hashlib.sha256(json.dumps({'basis': basis, 'changes': changes}, sort_keys=True).encode()).hexdigest()
    return {'planDigest': digest, 'basis': basis, 'changes': changes,
            'compileContractPins': {c: pins[c.casefold()] for c in sorted(contracts)},
            'remaining': ['Materialize meaningful behavior tests', 'Restore through selected tooling and retain locks',
                          'Build/evaluate exact architecture inventory', 'Execute selected tests; zero tests remain failure']}


def apply(root, relative, digest):
    plan = preview(root, relative)
    require(plan['planDigest'] == digest, 'PKA020 test scaffold inputs changed; review a fresh preview')
    target = inside(root, relative)
    original = (root / 'eng/architecture.json').read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        # Exclusive creation protects a concurrent consumer-authored project.
        with target.open('xb') as stream:
            stream.write(plan['changes'][relative].encode())
        created = True
        descriptor, temporary = tempfile.mkstemp(dir=root / 'eng', prefix='.test-owner-', suffix='.tmp')
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(plan['changes']['eng/architecture.json'])
            require((root / 'eng/architecture.json').read_bytes() == original, 'PKA020 architecture changed during scaffold; review again')
            os.replace(temporary, root / 'eng/architecture.json')
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except Exception:
        # Remove only our unchanged newly created project; never concurrent edits.
        if created and target.is_file() and target.read_bytes() == plan['changes'][relative].encode():
            target.unlink()
        raise
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    parser.add_argument('--project', required=True)
    parser.add_argument('--apply-digest')
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    try:
        result = apply(root, args.project, args.apply_digest) if args.apply_digest else preview(root, args.project)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
