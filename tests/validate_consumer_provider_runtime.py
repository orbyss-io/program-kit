"""Bounded native checks using the actual consumer recipe renderer and preparation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from validate_effective_dependency_context import EffectiveContextTests, ROOT, load_module, write_json
import bootstrap_compatibility
from compatibility_process import run


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('foundation-activation', 'bff-keycloak'))
    args = parser.parse_args()
    fixture = EffectiveContextTests()
    fixture.setUp()
    root = ROOT / 'artifacts/consumer-provider-runtime' / uuid.uuid4().hex[:8]
    shutil.copytree(fixture.root, root)
    fixture.root = root
    fixture.selection = root / 'docs/architecture/building-block-selection.json'
    catalog = fixture.selected()
    for extension in ('program-kit-governance', 'program-kit-dotnet'):
        shutil.copytree(ROOT / 'extensions' / extension, root / '.specify/extensions' / extension, dirs_exist_ok=True)
    decisions = fixture.decisions
    sdk = json.loads((root / '.specify/extensions/program-kit-dotnet/templates/dotnet/files/global.json').read_text())['sdk']['version']
    decisions.update(web={'secure_profile': 'bff-cookie-v1'}, toolchain={'source': 'default', 'pins': {'dotnet-sdk': sdk}})
    write_json(root / 'docs/architecture/bootstrap-decisions.json', decisions)
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
    from public_availability import verify_oci
    host = catalog['packages']['oci:ghcr.io/orbyss-io/foundation-host']
    image = verify_oci(host, catalog['sources'][host['source']])['reference']
    renderer = load_module(root / '.specify/extensions/program-kit-governance/scripts/managed_provider_probes.py')
    results = {}
    for kind in ([args.kind] if args.kind else ('foundation-activation', 'bff-keycloak')):
        recipe = renderer.render(root, kind, kind, image)
        contract = json.loads((root / recipe['recipe']).with_suffix('.contract.json').read_text())
        scratch = root / ('scratch-' + kind)
        scratch.mkdir()
        inputs, plan = bootstrap_compatibility.prepare(root, scratch, contract)
        write_json(scratch / 'preparation-inputs.json', inputs)
        with (scratch / 'native.stdout').open('wb') as stdout, (scratch / 'native.stderr').open('wb') as stderr:
            try:
                bootstrap_compatibility.restore(root, scratch, timeout=300, stdout=stdout, stderr=stderr)
                code = run([sys.executable, str(root / recipe['recipe'])], scratch, stdout, stderr, 600)
                if code: raise ValueError('Native recipe failed with exit ' + str(code))
                from phase_obligations import test_results
                cases = test_results(scratch / 'compatibility-results.xml', 'junit')
                if not all(cases.get(case) is True for case in renderer.CASES[kind]):
                    raise ValueError('Native recipe omitted required separate mechanism checks')
                results[kind] = {'status': 'passed', 'cases': renderer.CASES[kind]}
            except Exception as error:
                results[kind] = {'status': 'failed', 'error': str(error)}
                print(kind + ': ' + str(error))
        write_json(root / 'result.json', results)
        print(kind + ' evidence: ' + str(scratch))
    fixture.doCleanups()
    return 0 if all(result['status'] == 'passed' for result in results.values()) else 1


if __name__ == '__main__': raise SystemExit(main())
