"""Maintained bootstrap tool/runtime checks; shared sync owns all package restores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from compatibility_diagnostics import sanitize
from compatibility_process import run


def catalog():
    return {
        'dotnet-runtime': {'case': 'Managed.dotnet_runtime', 'proves': 'selected SDK builds and executes a minimal program; no consumer behavior'},
        'browser-runtime': {'case': 'Managed.browser_runtime', 'proves': 'selected Node/Playwright launches selected browser engines; no UI acceptance'},
        'foundation-host': {'case': 'Managed.foundation_host', 'proves': 'published local image executes its ASP.NET runtime; no consumer shell activation'},
        'foundation-activation': {'case': 'PublishedHost.exact_image_activation', 'proves': 'synthetic package activation, shell replacement, HTTP/OpenAPI and restart on the published image; no consumer behavior', 'requires': '--host-image with registry-verified selected release digest'},
        'bff-keycloak': {'case': 'Identity.code_flow_permission_negatives_and_logout', 'proves': 'selected published BFF and local Keycloak code flow, 401/403/authorized endpoint, cookie/storage and logout checks; no consumer membership or complete web assurance', 'requires': '--host-image with registry-verified selected release digest; pinned local Keycloak and Chromium'},
        'ef-postgresql': {'case': 'PostgreSql.atomic_expected_revision_conflict', 'proves': 'selected EF/Npgsql and exact PostgreSQL server write/read, stale-revision rejection, rollback and restart; no consumer schema, migrations or business policy', 'requires': 'selected ef-postgresql owner; exact image from provider_inputs.persistence_runtimes available locally'},
    }


def render(root: Path, kind: str, identity: str, engines=('chromium',), host_image=None):
    import re
    if kind not in catalog() or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,100}', identity):
        raise ValueError('Select a maintained recipe ID and safe prerequisite identity')
    if not engines or not set(engines) <= {'chromium', 'webkit', 'firefox'}:
        raise ValueError('Select explicit supported browser engines')
    if kind in {'foundation-activation', 'bff-keycloak', 'ef-postgresql'}:
        from managed_provider_probes import render as render_provider
        return render_provider(root, kind, identity, host_image)
    directory = root / 'docs/architecture/compatibility'
    directory.mkdir(parents=True, exist_ok=True)
    recipe = directory / (identity + '.py')
    config = directory / (identity + '.inputs.json')
    contract_path = recipe.with_suffix('.contract.json')
    if any(p.exists() for p in (recipe, config, contract_path)):
        raise ValueError('Recipe already exists; preserve reviewed inputs or use a new identity')
    extensions = Path(__file__).resolve().parents[2]
    pins = json.loads((root / 'docs/architecture/bootstrap-decisions.json').read_text())['toolchain']['pins']
    parameters = {'kind': kind, 'engines': list(engines)}
    fixtures = {'managed-probe.json': config.relative_to(root).as_posix()}
    targets = []
    if kind == 'dotnet-runtime':
        sdk = pins['dotnet-sdk']
        parameters['sdk'] = sdk
        project = directory / (identity + '.csproj')
        program = directory / (identity + '.cs')
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net' + sdk.split('.')[0] + '.0</TargetFramework></PropertyGroup></Project>\n')
        program.write_text('System.Console.WriteLine("PROGRAM_KIT_RUNTIME_OK");\n')
        fixtures.update({'Probe.csproj': project.relative_to(root).as_posix(), 'Program.cs': program.relative_to(root).as_posix()})
        targets = ['Probe.csproj']
    elif kind == 'browser-runtime':
        parameters['node'] = pins['node']
        package = directory / (identity + '.package.json')
        source = extensions / 'program-kit-dotnet/templates/dotnet/web-profiles/common/.program-kit/eng/web/package.json'
        content = json.loads(source.read_text(encoding='utf-8'))
        for name in content['devDependencies']:
            if name in pins:
                content['devDependencies'][name] = pins[name]
        package.write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8')
        fixtures['package.json'] = package.relative_to(root).as_posix()
        targets = ['package.json']
    else:
        source = extensions / 'program-kit-building-blocks/references/orbyss-building-blocks.json'
        entry = json.loads(source.read_text())['packages']['oci:ghcr.io/orbyss-io/foundation-host']
        parameters['image'] = entry['packageId'] + ':' + entry['materialization']['tagTemplate'].format(version=entry['version'])
    config.write_text(json.dumps(parameters, indent=2) + '\n')
    recipe.write_text("from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[3] / '.specify/extensions/program-kit-governance/scripts'))\nfrom managed_compatibility import probe\nraise SystemExit(probe(Path.cwd()))\n")
    contract = {'schemaVersion': 1, 'checks': [{'id': kind, 'kind': 'runtime-compatibility', 'testCases': [catalog()[kind]['case']]}],
                'fixtures': fixtures, 'dependencyTargets': targets}
    contract_path.write_text(json.dumps(contract, indent=2) + '\n')
    return {'id': identity, 'recipe': recipe.relative_to(root).as_posix(), 'timeout': 180}


def command(root, arguments, *, expected=None):
    if arguments[0] in {'node', 'npm', 'dotnet'}:
        evidence = root / '.program-kit/evidence/toolchain.json'
        toolchain = json.loads(evidence.read_text(encoding='utf-8')) if evidence.is_file() else {}
        prefix = toolchain.get('commands', {}).get(arguments[0])
        if not toolchain.get('satisfied') or not prefix:
            raise ValueError('needs-provisioning: shared sync has no satisfied ' + arguments[0] + ' toolchain receipt')
    else:
        executable = shutil.which(arguments[0])
        if not executable:
            raise ValueError('needs-provisioning: ' + arguments[0] + ' is unavailable on PATH')
        prefix = [executable]
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        code = run([*prefix, *arguments[1:]], root, stdout, stderr, 90)
        stdout.seek(0); stderr.seek(0)
        output = sanitize((stdout.read(65536) + stderr.read(65536)).decode('utf-8', errors='replace'))
    if code or expected and expected not in output:
        raise ValueError(arguments[0] + ' ' + ' '.join(arguments[1:]) + '\nexit=' + str(code) + '\n' + output)
    return output


def probe(root):
    settings = json.loads((root / 'managed-probe.json').read_text())
    kind = settings['kind']
    suite = ET.Element('testsuite', name='ProgramKitManagedCompatibility')
    case = ET.SubElement(suite, 'testcase', classname='Managed', name=catalog()[kind]['case'].split('.', 1)[1])
    code = 0
    try:
        if kind == 'dotnet-runtime':
            command(root, ['dotnet', '--version'], expected=settings['sdk'])
            command(root, ['dotnet', 'build', 'Probe.csproj', '--no-restore', '--nologo'])
            command(root, ['dotnet', 'run', '--project', 'Probe.csproj', '--no-build', '--no-restore'], expected='PROGRAM_KIT_RUNTIME_OK')
        elif kind == 'browser-runtime':
            command(root, ['node', '--version'], expected='v' + settings['node'])
            script = root / 'browser-probe.mjs'
            script.write_text("import { chromium, webkit, firefox } from '@playwright/test';\nconst engines={chromium,webkit,firefox};\nfor(const name of " + json.dumps(settings['engines']) + ") { const browser=await engines[name].launch(); try {const page=await browser.newPage(); await page.setContent('<button>probe</button>'); if(await page.getByRole('button',{name:'probe'}).count()!==1) throw new Error('DOM access failed: '+name);} finally {await browser.close();}}\nconsole.log('PROGRAM_KIT_BROWSER_OK');\n")
            command(root, ['node', str(script)], expected='PROGRAM_KIT_BROWSER_OK')
        elif kind == 'foundation-host':
            command(root, ['docker', 'image', 'inspect', settings['image']])
            command(root, ['docker', 'run', '--rm', '--pull=never', '--network=none', '--entrypoint=dotnet', settings['image'], '--list-runtimes'], expected='Microsoft.AspNetCore.App')
    except (ValueError, OSError) as error:
        code = 1
        reason = sanitize(str(error))
        ET.SubElement(case, 'failure', message=reason[:512]).text = reason
        print(reason, file=sys.stderr)
    ET.ElementTree(suite).write(root / 'compatibility-results.xml', encoding='utf-8', xml_declaration=True)
    return code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['catalog', 'render'])
    parser.add_argument('--kind', choices=list(catalog()))
    parser.add_argument('--id')
    parser.add_argument('--engines', default='chromium')
    parser.add_argument('--host-image')
    args = parser.parse_args()
    print(json.dumps(catalog() if args.command == 'catalog' else render(Path.cwd().resolve(), args.kind, args.id, tuple(args.engines.split(',')), args.host_image)))
