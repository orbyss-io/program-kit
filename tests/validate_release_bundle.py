"""Offline bundle production/admission and published-runtime boundary checks; no agent."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
sys.path.insert(0, str(TEMPLATE / 'eng'))
import release_bundle as bundle
from live.v2.lending_host import unpack_release_bundle, PublishedLendingHost, LendingHost
from live.v2.common import LiveContractError


class ReleaseBundleTests(unittest.TestCase):
    def test_native_portable_closure_preserves_framework_dependencies_and_combines_host_minima(self):
        self.write('NuGet.config', '<configuration><packageSources><clear/><add key="public" '
                   'value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
        packages = self.stage / 'packages'
        packages.mkdir(parents=True)
        root = packages / 'Fixture.1.0.0.nupkg'
        with zipfile.ZipFile(root, 'w') as archive:
            archive.writestr('Fixture.nuspec', '<package><metadata><id>Fixture</id><version>1.0.0</version>'
                '<authors>fixture</authors><description>Native closure regression</description><dependencies>'
                '<group targetFramework="net10.0"><dependency id="Microsoft.Extensions.Configuration.Binder" version="10.0.12"/>'
                '<dependency id="Microsoft.OpenApi" version="2.12.0"/></group></dependencies></metadata></package>')
            archive.writestr('lib/net10.0/Fixture.dll', b'restore-only fixture')
            archive.writestr('orbyss-foundation/feature.json', json.dumps({'schemaVersion':1, 'packageId':'Fixture',
                'identity':'Fixture', 'hostProvidedDependencies':[
                    {'packageId':'Microsoft.Extensions.Configuration.Abstractions', 'minimumVersion':'10.0.0'},
                    {'packageId':'Microsoft.Extensions.Configuration', 'minimumVersion':'10.0.0'}]}))
        identities = {('Fixture', '1.0.0'):root}
        bundle.complete_external_closure(self.root, self.stage, identities, {})
        actual = {identity.casefold():version for identity, version in identities}
        self.assertEqual('10.0.12', actual['microsoft.extensions.configuration.abstractions'])
        self.assertEqual('10.0.12', actual['microsoft.extensions.configuration'])
        self.assertIn('system.text.json', actual)  # net10 pruning must not erase portable package dependencies.
        self.assertNotIn('programkit.internal.hostrequirements', actual)
        evidence = json.loads((self.root / 'artifacts/program-kit/selected-root-restore.json').read_text())
        self.assertFalse(evidence['packagePruningEnabled'])
        self.assertEqual([], evidence['diagnosticCodes'])
        self.assertEqual({'Fixture':'1.0.0'}, evidence['roots'])

    def test_signed_nuget_identity_uses_native_content_bytes_and_rejects_tampering(self):
        project = self.root / 'signed-package.csproj'
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
                           '</PropertyGroup><ItemGroup><PackageDownload Include="Microsoft.AspNetCore.Authentication.OpenIdConnect" '
                           'Version="[10.0.12]" /></ItemGroup></Project>', encoding='utf-8')
        restored = subprocess.run(['dotnet', 'restore', str(project), '--packages', str(self.root / 'cache'),
                                   '--source', 'https://api.nuget.org/v3/index.json'],
                                  cwd=self.root, capture_output=True, text=True, timeout=180)
        self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)
        folder = self.root / 'cache/microsoft.aspnetcore.authentication.openidconnect/10.0.12'
        archive = folder / 'microsoft.aspnetcore.authentication.openidconnect.10.0.12.nupkg'
        expected = json.loads((folder / '.nupkg.metadata').read_text())['contentHash']
        import base64
        literal = base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode('ascii')
        self.assertNotEqual(expected, literal)  # Reproduces the real selected-root failure.
        self.assertEqual(expected, bundle.nuget_content_hash(self.root, archive))
        changed = self.root / 'changed-signed-package.nupkg'
        shutil.copyfile(archive, changed)
        with zipfile.ZipFile(changed, 'a') as writer:
            writer.writestr('tampered-payload.txt', 'changed payload')
        try:
            self.assertNotEqual(expected, bundle.nuget_content_hash(self.root, changed))
        except ValueError:
            pass  # A structurally invalid signed archive is also rejected.

    def test_local_nuget_source_does_not_use_http_and_requires_exact_identity(self):
        feed = self.root / 'local-feed'
        feed.mkdir()
        package = feed / 'Example.Feature.1.2.3.nupkg'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('Example.Feature.nuspec', '<package><metadata><id>Example.Feature</id><version>1.2.3</version></metadata></package>')
        destination = self.root / 'resolved.nupkg'
        with patch.object(bundle.urllib.request, 'urlopen', side_effect=AssertionError('Local source must not use HTTP')):
            bases = bundle.package_base_addresses([str(feed)])
            bundle.download_package('Example.Feature', '1.2.3', bases, destination)
            self.assertEqual(package.read_bytes(), destination.read_bytes())
            with self.assertRaises(FileNotFoundError):
                bundle.download_package('Example.Feature', '9.9.9', bases, destination)
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('Example.Feature.nuspec', '<package><metadata><id>Different</id><version>1.2.3</version></metadata></package>')
            with self.assertRaisesRegex(ValueError, 'differs from requested'):
                bundle.download_package('Example.Feature', '1.2.3', bases, destination)

    def test_installed_bundle_tool_includes_its_legacy_descriptor_bridge(self):
        with tempfile.TemporaryDirectory(prefix='installed-bundle-tool-') as directory:
            target = Path(directory)
            result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                                     '--target', str(target), '--profile-selected', '--foundation-host-accepted',
                                     '--building-block-sources-approved', '--web-profile', 'none'], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            installed = target / 'eng/legacy-feature-bridge.json'
            self.assertEqual((TEMPLATE / 'eng/legacy-feature-bridge.json').read_bytes(), installed.read_bytes())
            result = subprocess.run([sys.executable, '-I', '-c',
                                     'import sys;sys.path.insert(0,sys.argv[1]);import release_bundle;'
                                     'assert release_bundle.LEGACY_FEATURE_BRIDGE["packageVersions"] == ["0.2.2","0.2.3"]',
                                     str(target / 'eng')], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='release-bundle-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'artifacts/release-bundle'
        self.packages = self.root / 'artifacts/packages'
        self.packages.mkdir(parents=True)
        self.write('VERSION', '1.2.3\n')
        self.write('eng/application-handoff.json', {'schemaVersion': 1, 'applicationId': 'example.release'})
        self.write('hostsettings.json', {})
        self.write('nuplane.settings.json', {'Nuplane': {'Setup': {'Feeds': []}, 'Loading': {'Enabled': True}}})
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {}}}}})
        self.write('NuGet.config', '<configuration><packageSources /></configuration>')
        self.write('Directory.Packages.props', '<Project/>')
        patcher = patch.dict(os.environ, {'GITHUB_SHA': 'a' * 40})
        patcher.start(); self.addCleanup(patcher.stop)
        self.image = 'ghcr.io/orbyss-io/foundation-host'
        self.digest = 'sha256:' + 'b' * 64
        self.descriptor = self.root / 'artifacts/application-bundle.json'

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')

    def produce(self):
        with patch.object(bundle, 'package_base_addresses', return_value=[]), patch.object(bundle, 'download_package', side_effect=AssertionError('unexpected feed access')):
            bundle.stage(self.root, self.packages, self.stage)
        bundle.describe(self.root, self.stage, self.image, 'v0.2.0', self.digest, self.descriptor)
        return self.descriptor.with_suffix('.zip')

    def test_configuration_only_bundle_runs_through_real_producer_and_admission(self):
        archive = self.produce()
        manifest = unpack_release_bundle(archive, self.root / 'admitted')
        self.assertEqual(manifest['application']['version'], '1.2.3')
        self.assertEqual(manifest['hostImage']['tag'], 'v0.2.0')
        self.assertEqual(manifest['runtimeClosure']['packageCount'], 0)
        self.assertEqual(json.loads((self.root/'admitted/hostsettings.json').read_text())['Nuplane'],
                         json.loads((self.root/'nuplane.settings.json').read_text())['Nuplane'])
        self.assertEqual((self.root/'hostsettings.json').read_text(), '{}')
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), archive.with_suffix('.zip.sha256').read_text().split()[0])

    def test_bundled_feed_package_is_hash_bound(self):
        with zipfile.ZipFile(self.packages/'Example.1.0.0.nupkg', 'w') as z:
            z.writestr('Example.nuspec', '<package><metadata><id>Example</id><version>1.0.0</version></metadata></package>')
            z.writestr('orbyss-foundation/feature.json', json.dumps({'schemaVersion':1, 'packageId':'Example',
                'identity':'Example', 'featureDependencies':[], 'runtimeDependencies':[], 'routes':[]}))
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'Example': {}}}}}})
        archive = self.produce()
        manifest = unpack_release_bundle(archive, self.root/'admitted')
        self.assertEqual(manifest['runtimeClosure']['packageCount'], 1)

    def test_removed_and_unselected_output_packages_do_not_enter_configuration_only_bundle(self):
        for identity in ('Removed.Feature', 'Unnecessary.Composition'):
            with zipfile.ZipFile(self.packages / (identity+'.1.0.0.nupkg'), 'w') as z:
                z.writestr(identity+'.nuspec', '<package><metadata><id>'+identity+'</id><version>1.0.0</version></metadata></package>')
        archive = self.produce()
        manifest = unpack_release_bundle(archive, self.root/'admitted')
        self.assertEqual(manifest['runtimeClosure']['packageCount'], 0)

    def test_same_package_identity_with_different_bytes_is_rejected(self):
        paths = []
        for suffix in ('one', 'two'):
            path = self.packages / (suffix+'.nupkg'); paths.append(path)
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('Example.nuspec', '<package><metadata><id>Example</id><version>1.0.0</version></metadata></package>')
                z.writestr('content/value.txt', suffix)
        identities = {}; bundle.register_package(identities, paths[0])
        with self.assertRaisesRegex(ValueError, 'PKR014.*bytes'):
            bundle.register_package(identities, paths[1])

    def test_explicit_library_root_requires_current_source_and_exact_packed_version(self):
        self.write('Directory.Build.props', '<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit></PropertyGroup></Project>')
        self.write('src/Library/Library.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><PackageId>Imported.PureCore</PackageId></PropertyGroup></Project>')
        self.write('src/Library/Value.cs', 'namespace Library; public static class Value { public const int Number = 42; }')
        packed = subprocess.run(['dotnet','pack','src/Library/Library.csproj','-c','Release','-p:Version=1.2.3','-o',str(self.packages)],
                                cwd=self.root, capture_output=True, text=True, timeout=120)
        self.assertEqual(0, packed.returncode, packed.stdout+packed.stderr)
        for identity in ('Removed.Feature', 'Unselected.Runtime'):
            with zipfile.ZipFile(self.packages/(identity+'.1.2.3.nupkg'), 'w') as archive:
                archive.writestr(identity+'.nuspec', '<package><metadata><id>'+identity+'</id><version>1.2.3</version></metadata></package>')
        bundle.stage(self.root,self.packages,self.stage,root_packages=['Imported.PureCore'])
        self.assertEqual({('Imported.PureCore','1.2.3')}, {bundle.package_identity(path) for path in (self.stage/'packages').glob('*.nupkg')})
        with self.assertRaisesRegex(ValueError, 'PKR014.*current source'):
            bundle.stage(self.root,self.packages,self.stage,root_packages=['Removed.Feature'])
        self.write('VERSION','1.2.4\n')
        with self.assertRaisesRegex(ValueError, 'PKR014.*fresh packed output'):
            bundle.stage(self.root,self.packages,self.stage,root_packages=['Imported.PureCore'])

    def test_real_selected_roots_pack_exact_restore_closure_without_composition_and_replace_cleanly(self):
        """Actual SDK restore/pack; metadata admission is not a runtime-lifecycle claim."""
        feed = self.root/'feed'; feed.mkdir()
        self.write('NuGet.config', '<configuration><packageSources><clear/><add key="fixture" value="'+feed.as_posix()+'"/></packageSources>'
                   '<config><add key="globalPackagesFolder" value=".packages"/></config></configuration>')
        self.write('Directory.Build.props', '<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework><NuGetAudit>false</NuGetAudit>'
                   '<RestorePackagesWithLockFile>true</RestorePackagesWithLockFile><PackageId>$(MSBuildProjectName)</PackageId></PropertyGroup></Project>')
        self.write('eng/FeaturePackage.props', '<Project><PropertyGroup><PackageId>Imported.$(MSBuildProjectName)</PackageId></PropertyGroup></Project>')
        def command(*args):
            result = subprocess.run(['dotnet', *map(str,args)], cwd=self.root, capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=120)
            self.assertEqual(0, result.returncode, result.stdout+result.stderr)
        def project(name, extras='', feature=False, publisher=False):
            base = ('publisher/' if publisher else 'src/')+name+'/'
            self.write(base+name+'.csproj', '<Project Sdk="Microsoft.NET.Sdk">'
                       + ('<Import Project="../../eng/FeaturePackage.props"/>' if feature else '')
                       + '<PropertyGroup><Description>Native packaging regression</Description></PropertyGroup>'
                       + extras + ('<ItemGroup><None Include="feature.json" Pack="true" PackagePath="orbyss-foundation/feature.json"/></ItemGroup>' if feature else '')+'</Project>')
            self.write(base+'Value.cs', 'namespace '+name+'; public static class Value { public const int Number=42; }')
            if feature:
                self.write(base+'feature.json', {'schemaVersion':1, 'packageId':'Imported.'+name, 'identity':name,
                    'featureDependencies':[], 'runtimeDependencies':[], 'routes':[]})
            return base+name+'.csproj'
        dependency = project('PublicDependency', publisher=True)
        private = project('PrivateBuild', publisher=True)
        command('pack', dependency, '-c','Release','-p:Version=1.5.0','-o',feed)
        command('pack', private, '-c','Release','-p:Version=1.0.0','-o',feed)
        core = project('CoreHelper', '<PropertyGroup><PackageVersion>4.2.0</PackageVersion></PropertyGroup>')
        project('PrivateProjectBuild', '<PropertyGroup><IsPackable>false</IsPackable></PropertyGroup>')
        references = '<ItemGroup><ProjectReference Include="../CoreHelper/CoreHelper.csproj"/>' \
                     '<ProjectReference Include="../PrivateProjectBuild/PrivateProjectBuild.csproj" PrivateAssets="all" ReferenceOutputAssembly="false"/>' \
                     '<PackageReference Include="PublicDependency" Version="[1.0.0,2.0.0)"/>' \
                     '<PackageReference Include="PrivateBuild" Version="1.0.0" PrivateAssets="all"/></ItemGroup>'
        first = project('FeatureOne', references, True)
        second = project('FeatureTwo', '', True)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'FeatureOne':{}, 'FeatureTwo':{}}}}}})
        for path in (core, first, second):
            command('pack',path,'-c','Release','-p:Version=1.2.3','-o',self.packages)
        # Stale output remains present to verify root selection rather than cleanup luck.
        shutil.copyfile(feed/'PrivateBuild.1.0.0.nupkg', self.packages/'PrivateBuild.1.0.0.nupkg')
        with zipfile.ZipFile(self.packages/'Removed.1.0.0.nupkg','w') as z:
            z.writestr('Removed.nuspec','<package><metadata><id>Removed</id><version>1.0.0</version></metadata></package>')
        bundle.stage(self.root,self.packages,self.stage)
        expected = {('Imported.FeatureOne','1.2.3'),('Imported.FeatureTwo','1.2.3'),('CoreHelper','4.2.0'),('PublicDependency','1.5.0')}
        self.assertEqual(expected, {bundle.package_identity(path) for path in (self.stage/'packages').glob('*.nupkg')})
        unrelated = project('Unrelated', '<ItemGroup><PackageReference Include="PublicDependency" Version="[1.5.0]"/></ItemGroup>')
        command('restore', unrelated)
        unrelated_assets = self.root/'src/Unrelated/obj/project.assets.json'
        unrelated_value = json.loads(unrelated_assets.read_text())
        unrelated_value['libraries']['PublicDependency/1.5.0']['sha512'] = 'unselected graph is not byte authority'
        unrelated_assets.write_text(json.dumps(unrelated_value))
        bundle.stage(self.root,self.packages,self.stage)
        selected_assets = self.root/'src/FeatureOne/obj/project.assets.json'
        selected_bytes = selected_assets.read_bytes()
        selected_value = json.loads(selected_bytes)
        selected_value['libraries']['PublicDependency/1.5.0']['sha512'] = 'selected graph differs from package bytes'
        selected_assets.write_text(json.dumps(selected_value))
        with self.assertRaisesRegex(ValueError, 'PKR014.*bytes differ'):
            bundle.stage(self.root,self.packages,self.stage)
        selected_assets.write_bytes(selected_bytes)
        bundle.stage(self.root,self.packages,self.stage)
        closure = self.root/bundle.runtime_closure.EVIDENCE
        bundle.runtime_closure.validate(self.root,self.stage,closure,bundle.PROGRAM_KIT_VERSION)
        self.write('eng/FeaturePackage.props', '<Project><PropertyGroup><PackageId>Changed.$(MSBuildProjectName)</PackageId></PropertyGroup></Project>')
        with self.assertRaisesRegex(ValueError, 'PKR022.*sourceInputs'):
            bundle.runtime_closure.validate(self.root,self.stage,closure,bundle.PROGRAM_KIT_VERSION)
        self.write('eng/FeaturePackage.props', '<Project><PropertyGroup><PackageId>Imported.$(MSBuildProjectName)</PackageId></PropertyGroup></Project>')
        # Same selected identity with different package bytes is inadmissible.
        duplicate = self.packages/'duplicate.nupkg'
        shutil.copyfile(self.packages/'Imported.FeatureOne.1.2.3.nupkg', duplicate)
        with zipfile.ZipFile(duplicate,'a') as z: z.writestr('content/tampered.txt','different bytes')
        with self.assertRaisesRegex(ValueError, 'PKR014.*bytes'):
            bundle.stage(self.root,self.packages,self.stage)
        duplicate.unlink()
        private_files = {'private/runtime.json': '{"connection":"private"}', 'data/accounts.json':'["owner"]', 'data/notes.db':'persisted bytes'}
        for name,value in private_files.items(): self.write(name,value)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'FeatureTwo':{}}}}}})
        bundle.stage(self.root,self.packages,self.stage)
        self.assertEqual({('Imported.FeatureTwo','1.2.3')}, {bundle.package_identity(path) for path in (self.stage/'packages').glob('*.nupkg')})
        self.assertEqual({'FeatureTwo':{}}, json.loads((self.stage/'shells.json').read_text())['CShells']['Shells']['default']['Features'])
        self.assertEqual(private_files, {name:(self.root/name).read_text() for name in private_files})
        self.assertFalse(list((self.root/'artifacts').glob('program-kit-release-bundle-*')), 'owned temporary staging must be cleaned')
        # A package-only publisher root has no consumer restore graph. Native NuGet
        # resolves its bounded range in an ephemeral, nonpackable restore input.
        external = project('ExternalFeature', '<ItemGroup><PackageReference Include="PublicDependency" Version="[1.0.0,2.0.0)"/></ItemGroup>', True, True)
        command('pack', external,'-c','Release','-p:Version=1.2.3','-o',self.packages)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'ExternalFeature':{}}}}}})
        bundle.stage(self.root,self.packages,self.stage)
        self.assertEqual({('Imported.ExternalFeature','1.2.3'),('PublicDependency','1.5.0')},
                         {bundle.package_identity(path) for path in (self.stage/'packages').glob('*.nupkg')})
        resolution = json.loads((self.root/'artifacts/program-kit/selected-root-restore.json').read_text())
        self.assertTrue(resolution['satisfied']); self.assertIn('PublicDependency/1.5.0', resolution['libraries'])
        self.assertFalse(list((self.root/'artifacts').glob('program-kit-selected-roots-*')))
        external_package = self.packages/'Imported.ExternalFeature.1.2.3.nupkg'
        original_external = external_package.read_bytes()
        with zipfile.ZipFile(external_package) as z:
            original_members = {name:z.read(name) for name in z.namelist()}
        for constraint in ('[9.0.0,10.0.0)', 'invalid-range'):
            with zipfile.ZipFile(external_package, 'w') as z:
                for name,value in original_members.items():
                    if name.endswith('.nuspec'):
                        document = bundle.ElementTree.fromstring(value)
                        for item in document.iter():
                            if item.tag.endswith('dependency') and item.attrib.get('id') == 'PublicDependency':
                                item.set('version', constraint)
                        value = bundle.ElementTree.tostring(document)
                    z.writestr(name,value)
            with self.assertRaisesRegex(ValueError,'PKR014.*selected-root restore failed'):
                bundle.stage(self.root,self.packages,self.stage)
            self.assertFalse(list((self.root/'artifacts').glob('program-kit-selected-roots-*')), 'failed owned restore input must be cleaned')
            self.assertFalse(json.loads((self.root/'artifacts/program-kit/selected-root-restore.json').read_text())['satisfied'])
        external_package.write_bytes(original_external)
        # Independently selected native roots resolving different concrete bytes/versions
        # cannot silently upgrade one another through a synthetic aggregate.
        command('pack', dependency, '-c','Release','-p:Version=2.5.0','-o',feed)
        project('FeatureTwo', '<ItemGroup><PackageReference Include="PublicDependency" Version="[2.5.0]"/></ItemGroup>',True)
        command('pack', second,'-c','Release','-p:Version=1.2.3','-o',self.packages)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'FeatureOne':{}, 'FeatureTwo':{}}}}}})
        with self.assertRaisesRegex(ValueError,'PKR014.*conflicting versions'):
            bundle.stage(self.root,self.packages,self.stage)

    def test_pack_inventory_rejects_source_changes_and_tampered_packages(self):
        inventory = self.packages/'program-kit-pack.json'
        bundle.runtime_closure.prepare_pack(self.root,self.packages)
        self.write('Directory.Build.props','<Project><PropertyGroup><DefineConstants>Changed</DefineConstants></PropertyGroup></Project>')
        with self.assertRaisesRegex(ValueError,'PKR023.*source inputs'):
            bundle.runtime_closure.seal_pack(self.root,self.packages)
        inventory.unlink()
        bundle.runtime_closure.prepare_pack(self.root,self.packages)
        self.write('eng/BuildHook.ps1', 'Write-Output "changed native build input"')
        with self.assertRaisesRegex(ValueError,'PKR023.*source inputs'):
            bundle.runtime_closure.seal_pack(self.root,self.packages)
        inventory.unlink()
        bundle.runtime_closure.prepare_pack(self.root,self.packages)
        bundle.runtime_closure.seal_pack(self.root,self.packages)
        bundle.stage(self.root,self.packages,self.stage,inventory=inventory)
        evidence = json.loads((self.root/bundle.runtime_closure.EVIDENCE).read_text())
        self.assertTrue(evidence['packSourceFreshness']['established'])
        bundle.runtime_closure.validate(self.root,self.stage,self.root/bundle.runtime_closure.EVIDENCE,bundle.PROGRAM_KIT_VERSION)
        with zipfile.ZipFile(self.packages/'injected.nupkg','w') as z:
            z.writestr('Injected.nuspec','<package><metadata><id>Injected</id><version>1.0.0</version></metadata></package>')
        with self.assertRaisesRegex(ValueError,'PKR023.*tampered'):
            bundle.stage(self.root,self.packages,self.stage,inventory=inventory)

    def test_same_inputs_produce_identical_archive(self):
        first = self.produce().read_bytes()
        self.assertEqual(first, self.produce().read_bytes())

    def test_conflicting_nuplane_authority_fails(self):
        self.write('hostsettings.json', {'Nuplane': {'Loading': {'Enabled': False}}})
        with self.assertRaisesRegex(ValueError, 'conflicting Nuplane'):
            self.produce()

    def test_missing_nuplane_is_not_silently_omitted(self):
        (self.root/'nuplane.settings.json').unlink()
        with self.assertRaises(FileNotFoundError): self.produce()

    def test_configuration_edit_requires_restaging_before_release(self):
        self.produce()
        self.write('nuplane.settings.json', {'Nuplane': {'Loading': {'Enabled': False}}})
        with self.assertRaisesRegex(ValueError, 'PKR022.*sourceConfiguration'):
            bundle.describe(self.root, self.stage, self.image, 'v0.2.0', self.digest, self.descriptor)

    def test_remote_feed_configuration_is_retained_without_claiming_activation(self):
        settings = {'Nuplane': {'Setup': {'Feeds': [{'Name': 'approved-feed', 'ServiceIndex': 'https://example.invalid/v3/index.json'}]}}}
        self.write('nuplane.settings.json', settings)
        self.produce()
        self.assertEqual(json.loads((self.stage/'nuplane.settings.json').read_text()), settings)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'Unresolved': {}}}}}})
        with self.assertRaisesRegex(ValueError, 'PKR009'): self.produce()

    def test_consumer_image_is_rejected(self):
        self.image = 'ghcr.io/example/consumer'
        with self.assertRaisesRegex(ValueError, 'consumer images are forbidden'): self.produce()

    def test_publisher_multi_feature_metadata_and_private_dependencies(self):
        package = self.packages / 'Publisher.1.0.0.nupkg'
        value = {'schemaVersion': 2, 'packageId': 'Publisher', 'features': [
            {'identity': name, 'featureDependencies': [], 'runtimeDependencies': [],
             'routes': ['/shared'] if name == 'One' else [], 'dormant': True}
            for name in ('One', 'Two')], 'hostProvidedDependencies': [
                {'packageId': 'Private.Runtime', 'minimumVersion': '1.2.3'}]}
        def pack(metadata, legacy=None):
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('Publisher.nuspec', '<package><metadata><id>Publisher</id><version>1.0.0</version></metadata></package>')
                archive.writestr('orbyss-foundation/feature.json', json.dumps(metadata))
                if legacy is not None: archive.writestr('program-kit/feature.json', json.dumps(legacy))
        pack(value)
        self.assertEqual([item['identity'] for item in bundle.package_features(package)], ['One', 'Two'])
        self.assertEqual(bundle.package_dependencies(package), {('Private.Runtime', '1.2.3')})
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'One': {}, 'Two': {}}}}}})
        bundle.validate_feature_closure(self.root / 'shells.json', {('Publisher', '1.0.0'): package})
        value['features'][1]['routes'] = ['/shared']
        pack(value)
        with self.assertRaisesRegex(ValueError, 'PKR012'):
            bundle.validate_feature_closure(self.root / 'shells.json', {('Publisher', '1.0.0'): package})
        pack(value, dict(value, packageId='Spoof'))
        with self.assertRaisesRegex(ValueError, 'conflicting'): bundle.package_features(package)
        value['features'][1]['identity'] = 'One'
        pack(value)
        with self.assertRaisesRegex(ValueError, 'repeated'): bundle.package_features(package)

    def test_modified_configuration_and_injected_host_binary_fail_admission(self):
        archive = self.produce()
        original = archive.read_bytes()
        for name, content in [('hostsettings.json', b'{}'), ('Orbyss.Foundation.Host.dll', b'fake'), ('../escape', b'bad')]:
            archive.write_bytes(original)
            with zipfile.ZipFile(archive) as z: files = {n:z.read(n) for n in z.namelist()}
            files[name] = content
            with zipfile.ZipFile(archive, 'w') as z:
                for n,v in files.items(): z.writestr(n,v)
            with self.assertRaises(LiveContractError): unpack_release_bundle(archive, self.root/'rejected')
            self.assertFalse((self.root/'rejected').exists())

    def test_runtime_mounts_individual_bundle_inputs_without_hiding_host(self):
        self.produce()
        host = PublishedLendingHost(self.stage, self.image+'@'+self.digest, self.root, self.root/'evidence', {})
        with patch.object(LendingHost, 'start', return_value=host): host.start()
        self.assertEqual(host.command[:2], ['docker','run'])
        self.assertEqual(host.command[-1], self.image+'@'+self.digest)
        self.assertNotIn('target=/app,', ' '.join(host.command))
        self.assertNotIn('build', host.command)
        self.assertIn('target=/app/hostsettings.json,readonly', ' '.join(host.command))

    def test_shipped_consumer_paths_cannot_publish_images(self):
        release = (TEMPLATE/'.github/workflows/application-release.yml').read_text()
        dev = (ROOT/'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/Dev.ps1').read_text()
        for forbidden in ('docker build', 'docker push', 'buildx', 'packages: write'):
            self.assertNotIn(forbidden, release)
        self.assertNotIn('docker build', dev)
        self.assertFalse((TEMPLATE/'Dockerfile').exists())
        self.assertIn('application-bundle.zip', release)
        nuplane = json.loads((TEMPLATE/'nuplane.settings.json').read_text())
        self.assertEqual(nuplane['Nuplane']['Setup']['Feeds'][0]['IncludePatterns'], ['*'],
                         'Validated consumer packages must not be excluded by an Orbyss-only filter')

    def test_upgrade_moves_only_the_old_managed_closure_reference(self):
        sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/scripts'))
        import dotnet_sync
        migrations = json.loads((ROOT/'extensions/program-kit-dotnet/templates/dotnet/migrations.json').read_text())['migrations']
        original = {'schemaVersion': 1, 'owner': 'consumer', 'contracts': [
            {'id':'api', 'packageClosure':'artifacts/runnable-host/packages', 'baseline':'contracts/v1.json'},
            {'id':'custom', 'packageClosure':'consumer/special', 'baseline':'contracts/other.json'}]}
        payload = json.dumps(original).encode()
        migrated = dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', payload, migrations)
        expected = json.loads(payload)
        expected['contracts'][0]['packageClosure'] = 'artifacts/release-bundle/packages'
        self.assertEqual(json.loads(migrated), expected)
        self.assertEqual(dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', migrated, migrations), migrated)
        native = json.dumps({'schemaVersion': 1, 'contracts': ['contracts/openapi/api.contract.json']}).encode()
        self.assertEqual(native, dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', native, migrations))
        invalid = json.dumps({'contracts': [42]}).encode()
        with self.assertRaises(ValueError):
            dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', invalid, migrations)


if __name__ == '__main__': unittest.main()
