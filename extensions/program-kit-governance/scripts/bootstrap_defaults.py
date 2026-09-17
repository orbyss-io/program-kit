"""Resolve missing choices before approval using the existing managed profile authorities.

No prose classification, consumer-file discovery, network access or approval mutation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

REGISTER = Path('docs/architecture/bootstrap-decisions.json')
POLICY = '.specify/extensions/program-kit-governance/references/default-adoption.md'


def resolve(intake: dict, register: dict) -> dict:
    value = deepcopy(register)
    profiles = set(value.get('selected_profiles', []))
    choices = value.setdefault('choices', [])

    def record(identity, decision, source='program-kit-default'):
        if not any(c['id'] == identity for c in choices):
            choices.append({'id': identity, 'decision': decision, 'source': source,
                            'rationale': 'Default or dependency resolution under ' + POLICY,
                            'override': 'Explicit consumer selection takes precedence.'})

    def unresolved(identity, question):
        items = value.setdefault('unresolved', [])
        if not any(item['id'] == identity for item in items):
            items.append({'id': identity, 'question': question, 'kind': 'design-decision',
                          'owner': 'Consumer architecture owner', 'due_stage': 'implementation',
                          'blocks': 'Dependent implementation',
                          'recommendation': 'Research and review a consumer-owned integration and its bounded verification; no managed capability is claimed.'})

    routing = intake.get('routing', {})
    languages = {v.casefold() for v in routing.get('languages', [])}
    web = value.get('web', {})
    browser = web.get('browser_ui') is True or bool(profiles & {'browser-web', 'typescript-web'})
    if 'web' not in value:
        browser = browser or bool(set(routing.get('capabilities', [])) & {'authenticated-browser-bff', 'browser-spa-pkce'})
    if browser:
        profiles.add('browser-web')
        profiles.add('ui-experience-v1')
        web = value.setdefault('web', {})
        web.setdefault('browser_ui', True)
        if 'secure_profile' not in web:
            web.update(secure_profile='bff-cookie-v1', profile_source='program-kit-default',
                       override_reason='', threat_model='program-kit-web-threat-model-v1',
                       security_evidence='program-kit-web-security-evidence-v1')
            record('secure-web-profile', 'bff-cookie-v1')
    authenticated = web.get('secure_profile') in {'bff-cookie-v1', 'spa-pkce-v1'}
    explicit_other_stack = languages - {'.net', 'c#', 'csharp', 'typescript', 'javascript', 'html', 'css'}
    consumer_integration = authenticated and explicit_other_stack and 'dotnet' not in profiles
    if consumer_integration:
        unresolved('consumer-authentication-integration', 'Resolve authentication integration for the explicit language constraint; managed Foundation/.NET integration has not been adopted.')
    # Browser-only anonymous scope does not need an invented backend. Otherwise an
    # absent language preference selects the supported managed application baseline.
    if (authenticated and not consumer_integration) or (not languages and profiles <= {'ui-experience-v1', 'browser-web', 'typescript-web'} and web.get('secure_profile') != 'none-v1'):
        profiles.add('dotnet')
        record('application-platform', '.NET / Foundation', 'derived-default' if authenticated else 'program-kit-default')
    if 'dotnet' in profiles and 'dotnet' not in value:
        value['dotnet'] = {'host_runtime': 'Orbyss.Foundation.Host', 'host_source': 'program-kit-default',
                           'program_kit_host_opt_out': False, 'opt_out_reason': ''}
        record('host-runtime', 'Published Orbyss.Foundation.Host image; consumer settings and package bundle')
    if 'dotnet' in profiles and not value.get('dotnet', {}).get('program_kit_host_opt_out'):
        acknowledgements = value.setdefault('acknowledgements', [])
        if not any(a['id'] in {'orbyss-building-block-dependencies', 'program-kit-preview-dependencies'} for a in acknowledgements):
            acknowledgements.append({'id': 'orbyss-building-block-dependencies', 'summary': 'Foundation uses independently pinned building-block packages and registry sources from the installed catalog; application release bundles contain settings, Nuplane configuration and optional package feeds.'})
    if value.get('dotnet', {}).get('program_kit_host_opt_out'):
        unresolved('consumer-host-integration', 'Select and verify the consumer-owned host integration; Program Kit does not supply its scaffold.')
    if authenticated and not consumer_integration and 'identity' not in value:
        value['identity'] = {'provider': 'keycloak', 'source': 'program-kit-default',
                             'scope': 'local-evaluation', 'production_trigger': 'before-production-deployment'}
        record('identity-provider', 'Keycloak managed local adapter; production hosting is deferred to deployment')
    path = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/scripts/persistence_selection.py'
    spec = importlib.util.spec_from_file_location('bootstrap_persistence_defaults', path)
    persistence = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(persistence)
    for owner in value.get('persistence', []):
        if owner.get('profile', 'auto') == 'auto':
            profile = persistence.resolve_profile(owner.get('storage'), dotnet='dotnet' in profiles)
            if profile is None:
                profile = 'custom'
                unresolved('consumer-persistence-' + owner['owner'], 'Select and verify a consumer-owned persistence provider for ' + str(owner.get('storage')))
            owner['profile'] = profile
            record('persistence-' + owner['owner'], profile)
    value['selected_profiles'] = sorted(profiles)
    return value


def apply(root: Path) -> dict:
    path = root / REGISTER
    current = json.loads(path.read_text(encoding='utf-8'))
    resolved = resolve(json.loads((root / 'docs/architecture/bootstrap-intake.json').read_text(encoding='utf-8')), current)
    if 'toolchain' not in resolved and resolved['selected_profiles']:
        from bootstrap_context import managed_profile_pin_authority
        pins = managed_profile_pin_authority(root, resolved)['pins']
        if pins:
            resolved['toolchain'] = {'source': 'program-kit-default', 'pins': pins, 'override_reason': ''}
    if resolved != current:
        approval = root / '.specify/governance/bootstrap-assessment-approval.json'
        if approval.is_file():
            raise ValueError('BOOTSTRAP-APPROVAL-BOUNDARY: default resolution cannot rewrite an approved register; reopen assessment through the workflow')
        path.write_text(json.dumps(resolved, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return {'changed': resolved != current, 'selected_profiles': resolved['selected_profiles']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    args = parser.parse_args()
    try:
        print(json.dumps(apply(Path(args.repository).resolve())))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
