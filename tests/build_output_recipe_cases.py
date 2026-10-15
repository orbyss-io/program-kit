"""Real SDK publication/copy/pack qualification using an ordinary owned executable."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(ENG))
import build_output_recipe as outputs
import repository_verification as verification
import repository_architecture as architecture


class BuildOutputRecipeTests(unittest.TestCase):
    def graph(self):
        return {'src/Owned.Tool/Owned.Tool.csproj': {'path': 'src/Owned.Tool/Owned.Tool.csproj',
                    'role': 'implementation', 'projectReferences': []},
                'src/Owned.Provider/Owned.Provider.csproj': {'path': 'src/Owned.Provider/Owned.Provider.csproj',
                    'role': 'provider', 'projectReferences': [], 'buildProjectReferences': ['src/Owned.Tool/Owned.Tool.csproj'],
                    'buildOutputCopies': [{'project': 'src/Owned.Tool/Owned.Tool.csproj', 'directory': 'tools/owned-tool'}]},
                'tests/Consumer/Consumer.csproj': {'path': 'tests/Consumer/Consumer.csproj', 'role': 'test',
                    'projectReferences': ['src/Owned.Provider/Owned.Provider.csproj']}}

    def test_changed_lifecycle_destination_metadata_and_unknown_tasks_remain_refused(self):
        graph = self.graph(); parent = 'src/Owned.Provider/Owned.Provider.csproj'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            original = outputs.recipe(root, parent, graph)
            for defect in ('lifecycle', 'destination', 'metadata', 'unknown-task'):
                with self.subTest(defect=defect):
                    document = copy.deepcopy(original)
                    target = document.find('Target')
                    if defect == 'lifecycle':
                        target.set('AfterTargets', 'PrepareForBuild')
                    elif defect == 'destination':
                        target.find('Copy').set('DestinationFiles', 'outside')
                    elif defect == 'metadata':
                        document.find('.//TargetPath').text = 'tools/owned-tool/%(Filename)%(Extension)'
                    else:
                        ET.SubElement(target, 'Exec', Command='unowned command')
                    with self.assertRaisesRegex(ValueError, 'qualified recipe'):
                        outputs.derived_nodes(root, root / parent, document, graph)

    def test_foreign_source_overlapping_directories_and_custom_output_layout_are_refused(self):
        original = self.graph(); parent = 'src/Owned.Provider/Owned.Provider.csproj'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for defect in ('foreign', 'escape', 'overlap', 'output-layout'):
                with self.subTest(defect=defect):
                    graph = copy.deepcopy(original)
                    if defect == 'foreign':
                        graph[parent]['buildOutputCopies'][0]['project'] = 'outside.csproj'
                    elif defect == 'escape':
                        graph[parent]['buildOutputCopies'][0]['directory'] = 'tools/../data'
                    elif defect == 'overlap':
                        second = 'src/Second/Second.csproj'
                        graph[second] = {'path': second, 'role': 'implementation', 'projectReferences': []}
                        graph[parent]['buildProjectReferences'].append(second)
                        graph[parent]['buildOutputCopies'].append({'project': second, 'directory': 'tools/owned-tool/nested'})
                    else:
                        path = root / parent; path.parent.mkdir(parents=True)
                        path.write_text('<Project><PropertyGroup><OutputPath>../../data</OutputPath></PropertyGroup></Project>')
                    with self.assertRaisesRegex(ValueError, 'PKV003'):
                        outputs.recipe(root, parent, graph)

    def test_native_sdk_complete_outputs_incremental_freshness_removal_propagation_pack_and_pe(self):
        evidence = ROOT / 'artifacts/tests/build-output-copy' / uuid.uuid4().hex
        root = evidence / 'consumer'; root.mkdir(parents=True)
        graph = self.graph(); parent = 'src/Owned.Provider/Owned.Provider.csproj'
        def write(relative, content):
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding='utf-8')
        def command(arguments, name):
            result = subprocess.run(arguments, cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
            (evidence / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            self.assertEqual(0, result.returncode, 'Native build output qualification failed: ' + str(evidence / (name + '.log')))
            return result.stdout
        def inventory(directory):
            return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in directory.rglob('*') if path.is_file()}
        shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/global.json', root / 'global.json')
        write('NuGet.Config', '<configuration><packageSources><clear /></packageSources></configuration>')
        write('Directory.Build.props', '<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
              '<ImplicitUsings>enable</ImplicitUsings><NuGetAudit>false</NuGetAudit><RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>'
              '</PropertyGroup></Project>')
        write('src/Owned.Tool/Owned.Tool.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
              '<OutputType>Exe</OutputType><UseAppHost>false</UseAppHost></PropertyGroup><ItemGroup>'
              '<None Update="resources/**/*;NOTICE.txt" CopyToOutputDirectory="Always" /></ItemGroup></Project>')
        write('src/Owned.Tool/Version.cs', 'namespace Owned.Tool; public static class Version { public static int Current => 1; }')
        write('src/Owned.Tool/Program.cs', 'Console.WriteLine("Owned tool version " + Owned.Tool.Version.Current);')
        write('src/Owned.Tool/resources/locales/en/owned.txt', 'first exact owned content')
        write('src/Owned.Tool/NOTICE.txt', 'Synthetic owned-library fixture. MIT. No third-party payload.')
        write(parent, '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><PackageId>Owned.Provider</PackageId>'
              '<PackageLicenseExpression>MIT</PackageLicenseExpression></PropertyGroup><ItemGroup>'
              '<ProjectReference Include="../Owned.Tool/Owned.Tool.csproj" ReferenceOutputAssembly="false" /></ItemGroup></Project>')
        document = ET.parse(root / parent).getroot()
        for node in outputs.recipe(root, parent, graph):
            document.append(node)
        (root / parent).write_bytes(ET.tostring(document))
        write('src/Owned.Provider/Marker.cs', 'namespace Owned.Provider; public sealed class Marker;')
        write('tests/Consumer/Consumer.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
              '</PropertyGroup><ItemGroup><ProjectReference Include="../../src/Owned.Provider/Owned.Provider.csproj" /></ItemGroup></Project>')
        write('tests/Consumer/Program.cs', 'Console.WriteLine(typeof(Owned.Provider.Marker).FullName); '
              'if (!File.Exists(Path.Combine(AppContext.BaseDirectory,"tools/owned-tool/Owned.Tool.dll"))) throw new Exception("Missing owned binary"); '
              'Console.WriteLine("OWNED_PAYLOAD_PRESENT");')
        manifest = {'runtimeComposition': {'projects': list(graph.values()), 'bindings': []}}
        write('eng/architecture.json', json.dumps(manifest))
        sdk = command(['dotnet', '--version'], 'selected-sdk').strip()
        command(['dotnet', 'restore', 'tests/Consumer/Consumer.csproj', '--configfile', 'NuGet.Config'], 'restore')
        command(['dotnet', 'restore', 'tests/Consumer/Consumer.csproj', '--locked-mode', '--configfile', 'NuGet.Config'], 'locked-restore')
        command(['dotnet', 'build', 'tests/Consumer/Consumer.csproj', '--no-restore', '--nologo'], 'clean-build')
        publication = root / 'src/Owned.Provider/obj/ProgramKit.BuildOutputs/0'
        copied = root / 'src/Owned.Provider/bin/Debug/net10.0/tools/owned-tool'
        propagated = root / 'tests/Consumer/bin/Debug/net10.0/tools/owned-tool'
        original = inventory(publication)
        self.assertIn('Owned.Tool.dll', original); self.assertIn('NOTICE.txt', original)
        self.assertIn('Owned.Tool.runtimeconfig.json', original)
        self.assertIn('resources/locales/en/owned.txt', original)
        self.assertEqual(original, inventory(copied)); self.assertEqual(original, inventory(propagated))
        self.assertIn('Owned tool version 1', command(['dotnet', str(copied / 'Owned.Tool.dll')], 'actual-owned-executable'))
        self.assertIn('OWNED_PAYLOAD_PRESENT', command(['dotnet', 'run', '--project', 'tests/Consumer/Consumer.csproj', '--no-build'], 'actual-consumer'))
        fingerprint = verification.input_snapshot(root, 'tests/Consumer/Consumer.csproj', graph, stable_sources=True)
        write('src/Owned.Tool/Version.cs', 'namespace Owned.Tool; public static class Version { public static int Current => 2; }')
        write('src/Owned.Tool/resources/locales/en/owned.txt', 'changed exact owned content')
        command(['dotnet', 'build', 'tests/Consumer/Consumer.csproj', '--no-restore', '--nologo'], 'incremental-build')
        changed = inventory(publication)
        self.assertNotEqual(original['Owned.Tool.dll'], changed['Owned.Tool.dll'])
        self.assertNotEqual(fingerprint, verification.input_snapshot(root, 'tests/Consumer/Consumer.csproj', graph, stable_sources=True))
        self.assertEqual(changed, inventory(copied)); self.assertEqual(changed, inventory(propagated))
        self.assertIn('Owned tool version 2', command(['dotnet', str(propagated / 'Owned.Tool.dll')], 'actual-incremental-executable'))
        (root / 'src/Owned.Tool/resources/locales/en/owned.txt').rename(root / 'src/Owned.Tool/resources/locales/en/renamed.txt')
        command(['dotnet', 'build', 'tests/Consumer/Consumer.csproj', '--no-restore', '--nologo'], 'renamed-output-build')
        renamed = inventory(publication)
        self.assertNotIn('resources/locales/en/owned.txt', renamed)
        self.assertIn('resources/locales/en/renamed.txt', renamed)
        self.assertEqual(renamed, inventory(copied)); self.assertEqual(renamed, inventory(propagated))
        command(['dotnet', 'pack', parent, '--no-build', '--no-restore', '--configuration', 'Debug', '--output', 'artifacts/packages'], 'pack-current-output')
        package = next((root / 'artifacts/packages').glob('*.nupkg'))
        with zipfile.ZipFile(package) as archive:
            nuspec = ET.fromstring(archive.read(next(name for name in archive.namelist() if name.endswith('.nuspec'))))
            self.assertNotIn('Owned.Tool', [node.get('id') for node in nuspec.iter() if node.tag.rsplit('}', 1)[-1] == 'dependency'])
            payload = {name.removeprefix('tools/owned-tool/'): hashlib.sha256(archive.read(name)).hexdigest()
                       for name in archive.namelist() if name.startswith('tools/owned-tool/') and not name.endswith('/')}
        self.assertEqual(renamed, payload)
        architecture.execute(root, manifest, 'Debug')
        assembly_project = ENG / 'assembly_graph/AssemblyGraph.csproj'
        # The maintained inspector reads PE metadata; no producer assembly is loaded.
        metadata = json.loads(command(['dotnet', 'run', '--project', str(assembly_project), '--configuration', 'Release', '--no-build', '--',
            str(root / 'src/Owned.Provider/bin/Debug/net10.0/Owned.Provider.dll')], 'actual-pe-metadata'))
        self.assertNotIn('Owned.Tool', metadata[0]['references'])
        (evidence / 'result.json').write_text(json.dumps({'status': 'completed', 'applicationAcceptance': False,
            'sdk': sdk, 'sourceInputs': verification.input_snapshot(root, 'tests/Consumer/Consumer.csproj', graph, stable_sources=True),
            'original': original, 'changed': changed, 'renamed': renamed, 'packed': payload,
            'providerAssemblyReferences': metadata[0]['references']}, indent=2), encoding='utf-8')
