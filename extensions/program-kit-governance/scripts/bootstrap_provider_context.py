"""Read-only provider inputs for bootstrap closure; no restore or materialization."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import yaml


def project(root: Path, decisions: dict, *, require_selection=True) -> dict:
    sources = []

    def bind(relative):
        path = root / relative
        if not path.is_file():
            raise ValueError('PROVIDER-HANDOFF-MISSING: installed/selected input is missing: ' + relative)
        if not any(item['path'] == relative for item in sources):
            sources.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        return path

    result = {'sources': sources, 'selected_packages': [], 'identity_runtime': None, 'persistence_runtimes': [],
              'evidence_boundary': 'Selected identities and installed templates are planning inputs, not license admission or executed interoperability evidence. Inspect exact selected publisher/package license evidence; preserve unknowns and run the retained bounded proofs.'}
    catalog_relative = '.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
    selection_relative = 'docs/architecture/building-block-selection.json'
    catalog_path = None
    module = None
    managed_host = 'dotnet' in decisions.get('selected_profiles', []) and not decisions.get('dotnet', {}).get('program_kit_host_opt_out')
    catalog = None
    if (root / selection_relative).is_file() or managed_host:
        selection_path = bind(selection_relative) if (root / selection_relative).is_file() else None
        candidate_path = bind(catalog_relative)
        resolver_path = bind('.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        spec = importlib.util.spec_from_file_location('bootstrap_provider_resolver', resolver_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        selection = json.loads(selection_path.read_text(encoding='utf-8')) if selection_path else None
        effective = module.effective_dependency_context(root)
        catalog_path = Path(effective['catalogPath'])
        catalog = effective['catalog']
        for source in effective['sources']:
            bind(Path(source).relative_to(root.resolve()).as_posix())
        result['dependency_context'] = {key: effective[key] for key in
            ('authority', 'profile', 'qualification', 'resolutionSha256', 'sharedAbi')}
    if managed_host:
        catalog = catalog or json.loads((catalog_path or bind(catalog_relative)).read_text(encoding='utf-8'))
        relative = '.specify/extensions/program-kit-building-blocks/references/foundation-baseline-evidence.json'
        evidence = json.loads(bind(relative).read_text(encoding='utf-8'))
        version = catalog['families']['foundation']['releaseVersion']
        registry = module.profile_registry()
        index = json.loads(bind((registry / 'index.json').relative_to(root).as_posix()).read_text(encoding='utf-8'))
        identity = effective['profile']
        matched = (identity, index['profiles'][identity]) if effective['publisherKnowledge'] else None
        if matched:
            identity,entry = matched
            module.qualified_dependency_profile(registry,identity,json.loads(candidate_path.read_text(encoding='utf-8')))
            source = (registry / entry['knowledge']['path']).relative_to(root).as_posix()
            knowledge = json.loads(bind(source).read_text(encoding='utf-8'))
            declarations = [module.publisher_package_fact(registry,p) for p in knowledge['packages']]
            evidence = {'sourceCommit':knowledge['sourceCommit'],'hostImage':knowledge['hostImage'],
                'packageMetadata':declarations,'hostDistribution':{'noticeFiles':[p for p in knowledge['documents'] if p['publisherPath'] in {'LICENSE','THIRD-PARTY-NOTICES.md','src/Orbyss.Foundation.Host/NOTICE.md'}],
                'metadataExceptions':[{'id':'Foundation Host','resolution':'OCI distribution; full runtime/OS redistribution notices remain due before distribution.'}]},
                'maintenance':{'conclusion':'Exact public package, source and Host inputs qualified by the selected profile.'},
                'assessment':{'limits':['No blanket legal, security or support clearance; retain consumer-specific redistribution and acceptance obligations.']}}
            relative = source
            result['publisher_knowledge'] = {'profile':identity,'releaseVersion':version,'source':source,
                'query_command':'python .specify/extensions/program-kit-building-blocks/scripts/publisher_knowledge.py --profile '+identity,
                'packages':[p['id'] for p in knowledge['packages']],
                'guidance':'Query the exact package or publisher-relative source document needed for this stage. Do not bulk-read the knowledge bundle.'}
        elif evidence.get('releaseVersion') != version:
            raise ValueError('KIT-DEPENDENCY-EVIDENCE-DRIFT: installed default/selection uses Foundation ' + version
                             + ' but bundled source evidence covers ' + str(evidence.get('releaseVersion'))
                             + '; update the kit profile and its publisher knowledge together before running consumer closure.')
        result['managed_baseline_evidence'] = {'source': relative, 'releaseVersion': version,
            'sourceCommit': evidence['sourceCommit'], 'hostImage': evidence['hostImage'],
            'publisher': catalog['families']['foundation']['repository'],
            'packageMetadataCount': len(evidence['packageMetadata']),
            'distributionNoticeCount': len(evidence['hostDistribution']['noticeFiles']),
            'maintenance': evidence['maintenance'], 'assessment': evidence['assessment'],
            'metadataExceptions': evidence['hostDistribution']['metadataExceptions']}
    if module is not None and selection_path is not None:
        # Reuse the existing resolver including its Draft placement and catalog checks.
        # The returned in-memory plan is never written as an Accepted lock.
        plan = module.resolve(root, selection_path, catalog_path,
                              decisions.get('default_profile', {}).get('version', 'unspecified'),
                              require_accepted=selection['status'] == 'Accepted')
        packages = {p['packageKey']: p for t in plan['targets'] for p in t['packages']}
        result.update(
            selected_packages=[{k: p[k] for k in ('packageKey', 'packageId', 'family', 'ecosystem', 'version', 'source')}
                               for _, p in sorted(packages.items())],
            instances=plan['instances'], activations=plan['activations'],
            targets=[{k: t[k] for k in ('id', 'kind', 'path')} for t in plan['targets']],
            registry_sources=plan['registryRequirements'],
            publisher_sources={family: catalog['families'][family] for family in sorted({p['family'] for p in packages.values()})},
            configuration_requirements=plan['configurationRequirements'],
        )
    elif require_selection and (
        ('dotnet' in decisions.get('selected_profiles', []) and not decisions.get('dotnet', {}).get('program_kit_host_opt_out'))
        or decisions.get('web', {}).get('secure_profile') in {'bff-cookie-v1', 'spa-pkce-v1'}
    ):
        raise ValueError('PROVIDER-HANDOFF-MISSING: managed host/browser closure needs its architecture-owned building-block selection')
    identity = decisions.get('identity', {})
    # Interpret the known managed identity consistently without rewriting approved text.
    # Unknown providers and consumer-service scopes remain consumer-owned.
    if str(identity.get('provider', '')).strip().casefold() == 'keycloak' and identity.get('scope') == 'local-evaluation':
        relative = '.specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/deploy/compose.identity.yml'
        document = yaml.safe_load(bind(relative).read_text(encoding='utf-8'))
        image = document['services']['keycloak']['image']
        if not isinstance(image, str) or not re.fullmatch(r'.+:\d[^@\s]*@sha256:[0-9a-f]{64}', image):
            raise ValueError('PROVIDER-HANDOFF-MISSING: managed Keycloak image needs an exact tag and digest')
        result['identity_runtime'] = {'provider': 'keycloak', 'image': image, 'source': relative,
                                      'scope': decisions['identity'].get('scope', 'local-evaluation')}
    owners = decisions.get('persistence', [])
    postgres = [owner for owner in owners if owner.get('profile') == 'ef-postgresql']
    if postgres:
        base = '.specify/extensions/program-kit-dotnet/'
        relative = base + 'references/persistence-runtimes.json'
        runtime = json.loads(bind(relative).read_text(encoding='utf-8'))['profiles']['ef-postgresql']
        if not re.fullmatch(r'postgres@sha256:[0-9a-f]{64}', runtime.get('image', '')) or not runtime.get('version'):
            raise ValueError('PROVIDER-HANDOFF-MISSING: managed PostgreSQL needs an exact server version and digest')
        pins = {item.attrib['Include']: item.attrib['Version'] for item in
                ET.parse(bind(base + runtime['packagePins'])).iter('PackageVersion')}
        result['persistence_runtimes'].append({**runtime, 'profile': 'ef-postgresql', 'source': relative,
            'owners': [owner['owner'] for owner in postgres], 'packages': pins})
    return result
