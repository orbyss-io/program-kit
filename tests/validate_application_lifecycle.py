"""Exercise actual pinned CShells/Foundation lifecycle; never starts a coding agent."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import json
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks
from owned_fixture import FixtureDirectory
from live.v2.cli import supervisor_environment
from live.v2.common import LiveContractError
from live.v2.supervisor import run_supervised


def stage_passed(result, stderr, expected_failure):
    if result.timedOut or result.operatorCancellationRecorded or not result.cleanupComplete or not result.logsDrained:
        return False
    if expected_failure:
        lines = stderr.splitlines()
        expected_message = expected_failure if isinstance(expected_failure, str) else 'System.InvalidOperationException: policy ran before provider'
        return result.exitCode == 1 and bool(lines) and lines[0] == expected_message
    return result.exitCode == 0


def main():
    evidence = ROOT/'artifacts/application-lifecycle'/uuid.uuid4().hex
    evidence.mkdir(parents=True)
    catalog = blocks.new_project_catalog()
    shared = ET.parse(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Packages.props')
    shared_pins = {row.get('Include'): row.get('Version') for row in shared.iter('PackageVersion')}
    versions = {name: catalog['packages']['nuget:' + name]['version'] for name in
                ('Orbyss.Foundation.Tasks', 'Orbyss.Foundation.DomainEvents')}
    versions['CShells.AspNetCore'] = shared_pins['CShells.AspNetCore.Abstractions']
    result_record = {'packages': versions, 'checks': [], 'outcome': 'running'}
    with FixtureDirectory(native=True) as temporary:
        root = Path(temporary)
        shutil.copytree(ROOT/'tests/fixtures/application-lifecycle', root, dirs_exist_ok=True)
        shutil.copy2(ROOT/'extensions/program-kit-dotnet/templates/dotnet/files/global.json', root/'global.json')
        environment = supervisor_environment()
        environment['NUGET_PACKAGES'] = str(root/'cache')
        sources = []
        cached = Path.home()/'.nuget/packages'
        closures = [p for p in (ROOT/'artifacts/profile-update-native').glob('*/closure')
                    if all((p / (name.lower() + '.' + version + '.nupkg')).is_file()
                           for name, version in versions.items() if name.startswith('Orbyss.Foundation.'))]
        if cached.is_dir() and closures:
            config = ET.Element('configuration')
            feeds = ET.SubElement(config, 'packageSources'); ET.SubElement(feeds, 'clear')
            for number, path in enumerate((cached, closures[-1])):
                ET.SubElement(feeds, 'add', key='fixture-cache-'+str(number), value=str(path))
            ET.SubElement(ET.SubElement(config, 'packageSourceMapping'), 'clear')
            ET.ElementTree(config).write(root/'NuGet.Config', encoding='utf-8', xml_declaration=True)
        commands = [ ['dotnet', 'restore', str(root/'Probe.csproj'), *sources],
                     ['dotnet', 'run', '--project', str(root/'Probe.csproj'), '--no-restore'],
                     ['dotnet', 'run', '--project', str(root/'Probe.csproj'), '--no-restore', '--no-build', '--', '--break-schema-order'],
                     ['dotnet', 'run', '--project', str(root/'Probe.csproj'), '--no-restore', '--no-build', '--', '--missing-handler'],
                     ['dotnet', 'run', '--project', str(root/'Probe.csproj'), '--no-restore', '--no-build', '--', '--missing-dispatcher'] ]
        for number, command in enumerate(commands):
            try:
                process_evidence = evidence / str(number)
                result = run_supervised(command, cwd=root, environment=environment,
                                        evidence_directory=process_evidence, timeout_seconds=180)
                (process_evidence / 'process.json').write_text(json.dumps(result.as_dict(), indent=2)+'\n', encoding='utf-8')
                stdout = (process_evidence / result.stdout.path).read_text(encoding='utf-8', errors='replace')
                stderr = (process_evidence / result.stderr.path).read_text(encoding='utf-8', errors='replace')
            except (OSError, subprocess.SubprocessError, LiveContractError) as error:
                result_record.update(outcome='failed', diagnostic=type(error).__name__)
                (evidence/'result.json').write_text(json.dumps(result_record, indent=2)+'\n', encoding='utf-8')
                raise
            expected_failure = {2:'System.InvalidOperationException: policy ran before provider',
                                3:'Missing typed reaction registration observed.',
                                4:'Missing selected native dispatcher observed.'}.get(number, False)
            passed = stage_passed(result, stderr, expected_failure)
            result_record['checks'].append({'stage': ('restore', 'actual-lifecycle-and-native-events', 'ordering-regression-red', 'missing-handler-red', 'missing-dispatcher-red')[number], 'exitCode': result.exitCode, 'expectedFailure': expected_failure, 'passed': passed, 'timeoutSeconds': 180, 'process': result.as_dict()})
            result_record['outcome'] = 'running' if passed else 'failed'
            (evidence/'result.json').write_text(json.dumps(result_record, indent=2)+'\n', encoding='utf-8')
            print(stdout)
            if not passed:
                raise ValueError('Lifecycle stage failed or ordering mutation was not rejected; inspect ' + str(process_evidence))
            if number == 0:
                assets = json.loads((root/'obj/project.assets.json').read_text())
                for identity, version in result_record['packages'].items():
                    versions = {key.split('/', 1)[1] for key in assets['libraries'] if key.split('/', 1)[0] == identity}
                    if versions != {version}:
                        result_record.update(outcome='failed', diagnostic='resolved fixture package differs from exact pin: '+identity)
                        (evidence/'result.json').write_text(json.dumps(result_record, indent=2)+'\n', encoding='utf-8')
                        raise ValueError(result_record['diagnostic'])
                result_record['resolvedPackages'] = result_record['packages'].copy()
        result_record['outcome'] = 'passed'
        (evidence/'result.json').write_text(json.dumps(result_record, indent=2)+'\n', encoding='utf-8')
        print('Lifecycle evidence: ' + str(evidence))


if __name__ == '__main__': main()
