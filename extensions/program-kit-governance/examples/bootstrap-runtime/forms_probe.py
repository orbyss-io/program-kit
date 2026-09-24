"""Execute the existing source-bound public Forms and HostedPages probes.

The coordinator restores every dependency target first. Child tests exercise real
public producers, manifest/tamper admission, the React facade and hosted HTTP;
this is synthetic compatibility, not first-slice consumer acceptance.
"""
import json
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path.cwd()))  # Coordinator-copied, contract-bound helper.
from bounded_process import run


def main():
    for key in list(os.environ):
        if any(part in key.upper() for part in ['TOKEN', 'PASSWORD', 'SECRET', 'CREDENTIAL', 'CONNECTION_STRING']):
            os.environ.pop(key)
    root = Path.cwd()
    toolchain = json.loads(Path('.program-kit/evidence/toolchain.json').read_text())
    dotnet, node = toolchain['commands']['dotnet'], toolchain['commands']['node']
    suite = ET.Element('testsuite', name='Forms')
    def check(name, commands):
        case = ET.SubElement(suite, 'testcase', classname='Forms', name=name)
        try:
            for index, (command, cwd) in enumerate(commands):
                out, err = root / f'{name}-{index}.stdout', root / f'{name}-{index}.stderr'
                with out.open('wb') as stdout, err.open('wb') as stderr:
                    code = run(command, cwd, stdout, stderr, 180)
                if code:
                    print(out.read_text(encoding='utf-8', errors='replace')[-6000:])
                    print(err.read_text(encoding='utf-8', errors='replace')[-6000:])
                    raise RuntimeError(name + ': child exited ' + str(code))
        except Exception as error:
            ET.SubElement(case, 'failure', message=str(error))
            raise
        finally:
            ET.ElementTree(suite).write('compatibility-results.xml', encoding='utf-8', xml_declaration=True)
    check('producer_create_review_approve_publish', [([*dotnet, 'run', '--project', 'components/ComponentProbe.csproj', '--no-restore', '--', 'producer-results.xml'], root)])
    producer = ET.parse('producer-results.xml').getroot()
    assert len(producer.findall('testcase')) == 3 and not producer.findall('.//failure') and not producer.findall('.//skipped')
    check('trusted_manifest_and_tamper_rejection', [([*node, '--test', 'tests/release-integration.test.mjs'], root / 'web')])
    check('react_renderer_load', [([*node, 'tests/forms-browser/build.mjs'], root / 'web'),
        ([*node, 'tests/forms-browser/browser.mjs', '--engines=chromium,webkit'], root / 'web')])
    check('hosted_assets_public_bootstrap', [([*dotnet, 'run', '--project', 'components/hosted-pages/Probe.csproj', '--no-restore'], root)])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
