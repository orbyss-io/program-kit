"""Read-only provider inputs for bootstrap closure; no restore or materialization."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import yaml


def project(root: Path, decisions: dict, *, require_selection=True) -> dict:
    sources = []

    def bind(relative):
        path = root / relative
        if not path.is_file():
            raise ValueError('PROVIDER-HANDOFF-MISSING: installed/selected input is missing: ' + relative)
        sources.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        return path

    result = {'sources': sources, 'selected_packages': [], 'identity_runtime': None,
              'evidence_boundary': 'Selected identities and installed templates are planning inputs, not license admission or executed interoperability evidence. Inspect exact selected publisher/package license evidence; preserve unknowns and run the retained bounded proofs.'}
    selection_relative = 'docs/architecture/building-block-selection.json'
    if (root / selection_relative).is_file():
        selection_path = bind(selection_relative)
        catalog_path = bind('.specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json')
        resolver_path = bind('.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        spec = importlib.util.spec_from_file_location('bootstrap_provider_resolver', resolver_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        selection = json.loads(selection_path.read_text(encoding='utf-8'))
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
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
    if identity.get('provider') == 'keycloak' and identity.get('scope') == 'local-evaluation':
        relative = '.specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/deploy/compose.identity.yml'
        document = yaml.safe_load(bind(relative).read_text(encoding='utf-8'))
        image = document['services']['keycloak']['image']
        if not isinstance(image, str) or not re.fullmatch(r'.+:\d[^@\s]*@sha256:[0-9a-f]{64}', image):
            raise ValueError('PROVIDER-HANDOFF-MISSING: managed Keycloak image needs an exact tag and digest')
        result['identity_runtime'] = {'provider': 'keycloak', 'image': image, 'source': relative,
                                      'scope': decisions['identity'].get('scope', 'local-evaluation')}
    return result
