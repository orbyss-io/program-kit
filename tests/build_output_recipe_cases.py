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
ENG = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'
sys.path.insert(0, str(ENG))
import build_output_recipe as outputs
import repository_verification as verification
import repository_architecture as architecture
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import artifact_ownership as ownership
import json_schema


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

    def test_feature_ownership_schema_and_direct_reader_preserve_distinct_build_edges(self):
        graph = self.graph(); parent = 'src/Owned.Provider/Owned.Provider.csproj'; producer = 'src/Owned.Tool/Owned.Tool.csproj'
        graph.pop('tests/Consumer/Consumer.csproj')
        graph[producer].update(role='helper', packageReferences=[])
        graph[parent].update(role='implementation', featureIdentities=['Owned.Provider'], packageReferences=[])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); (root / '.specify').mkdir()
            feature = root / 'specs/owned'; feature.mkdir(parents=True)
            authority = 'docs/architecture/owned.md'; (root / authority).parent.mkdir(parents=True)
            (root / authority).write_text('Fictional accepted owner/tool placement. No human authority.')
            for path in graph:
                (root / path).parent.mkdir(parents=True)
                (root / path).write_text('<Project Sdk="Microsoft.NET.Sdk" />')
            manifest = {'schemaVersion': 1, 'feature': 'owned', 'profiles': ['dotnet'],
                'artifacts': [{'path': path, 'ownership': 'consumer-owned', 'classification': 'internal', 'lifecycle': 'source'} for path in graph],
                'runtimeComposition': {'authorities': [authority], 'projects': list(graph.values()), 'bindings': [], 'coreReferences': []}}
            schema_path = ROOT / 'extensions/program-kit-governance/references/artifact-ownership.schema.json'
            schema = json.loads(schema_path.read_text())
            self.assertTrue(json_schema.validate_value(manifest, schema, location=schema_path)['valid'])
            for metadata in ('ReferenceOutputAssembly="false"', '', 'OutputItemType="Analyzer"'):
                child = '<ReferenceOutputAssembly>false</ReferenceOutputAssembly>' if not metadata else ''
                (root / parent).write_text('<Project><ItemGroup><ProjectReference Include="../Owned.Tool/Owned.Tool.csproj" '
                                          + metadata + '>' + child + '</ProjectReference></ItemGroup></Project>')
                ownership.validate_runtime_composition(feature, manifest)
            graph[parent]['projectReferences'] = [producer]
            with self.assertRaisesRegex(ValueError, 'overlapping CLR/build'):
                ownership.validate_runtime_composition(feature, manifest)
            graph[parent]['projectReferences'] = []
            graph[producer]['buildProjectReferences'] = [parent]
            with self.assertRaisesRegex(ValueError, '[Cc]ycle'):
                ownership.validate_runtime_composition(feature, manifest, design_only=True)
            graph[producer].pop('buildProjectReferences')
            graph[parent]['buildOutputCopies'][0]['directory'] = 'tools/../data'
            with self.assertRaisesRegex(ValueError, 'owned tools'):
                ownership.validate_runtime_composition(feature, manifest, design_only=True)

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
        command([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                 '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                 '--building-block-sources-approved', '--web-profile', 'none'], 'installed-native-tools')
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
        manifest = {'runtimeComposition': {'projects': list(graph.values()), 'bindings': []}}
        original_intent = copy.deepcopy(manifest)
        next(row for row in original_intent['runtimeComposition']['projects'] if row['path'] == parent).pop('buildOutputCopies')
        write('config/program-kit/architecture.json', json.dumps(original_intent))
        document = ET.parse(root / parent).getroot()
        bad = copy.deepcopy(document)
        ET.SubElement(ET.SubElement(bad, 'Target', Name='UnreviewedCopy'), 'Exec', Command='must never execute')
        (root / parent).write_bytes(ET.tostring(bad))
        rejected = subprocess.run([sys.executable, str(root / 'scripts/repository_verification.py'), '--repository', str(root),
            '--scope', 'Affected', '--changed-path', parent, '--plan'], cwd=root, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(0, rejected.returncode)
        diagnostic = rejected.stdout + rejected.stderr
        self.assertIn('buildProjectReferences/buildOutputCopies', diagnostic)
        self.assertIn('scripts/build_output_recipe.py', diagnostic)
        self.assertIn(parent, diagnostic)
        (evidence / 'unsupported-target.log').write_text(diagnostic, encoding='utf-8')
        # The fixture explicitly replaces only its own known unreviewed target;
        # the product does not convert or waive arbitrary consumer customizations.
        (root / parent).write_bytes(ET.tostring(document))
        write('config/program-kit/architecture.json', json.dumps(manifest))
        preview = command([sys.executable, str(root / 'scripts/build_output_recipe.py'), '--repository', str(root),
                           '--project', parent], 'installed-recipe-preview')
        for node in ET.fromstring(preview):
            document.append(node)
        (root / parent).write_bytes(ET.tostring(document))
        write('src/Owned.Provider/Marker.cs', 'namespace Owned.Provider; public sealed class Marker;')
        write('tests/Consumer/Consumer.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
              '</PropertyGroup><ItemGroup><ProjectReference Include="../../src/Owned.Provider/Owned.Provider.csproj" /></ItemGroup></Project>')
        write('tests/Consumer/Program.cs', 'Console.WriteLine(typeof(Owned.Provider.Marker).FullName); '
              'if (!File.Exists(Path.Combine(AppContext.BaseDirectory,"tools/owned-tool/Owned.Tool.dll"))) throw new Exception("Missing owned binary"); '
              'Console.WriteLine("OWNED_PAYLOAD_PRESENT");')
        manifest = {'runtimeComposition': {'projects': list(graph.values()), 'bindings': []}}
        write('config/program-kit/architecture.json', json.dumps(manifest))
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
        command([sys.executable, str(root / 'scripts/repository_architecture.py'), '--repository', str(root),
                 '--manifest', 'config/program-kit/architecture.json', '--configuration', 'Debug',
                 '--output', 'artifacts/installed-architecture.xml'], 'installed-architecture')
        assembly_project = root / 'tools/program-kit/assembly_graph/AssemblyGraph.csproj'
        # The maintained inspector reads PE metadata; no producer assembly is loaded.
        metadata = json.loads(command(['dotnet', 'run', '--project', str(assembly_project), '--configuration', 'Release', '--no-build', '--',
            str(root / 'src/Owned.Provider/bin/Debug/net10.0/Owned.Provider.dll')], 'actual-pe-metadata'))
        self.assertNotIn('Owned.Tool', metadata[0]['references'])
        (evidence / 'result.json').write_text(json.dumps({'status': 'completed', 'applicationAcceptance': False,
            'sdk': sdk, 'sourceInputs': verification.input_snapshot(root, 'tests/Consumer/Consumer.csproj', graph, stable_sources=True),
            'original': original, 'changed': changed, 'renamed': renamed, 'packed': payload,
            'providerAssemblyReferences': metadata[0]['references']}, indent=2), encoding='utf-8')
