"""Offline public-delivery orchestration tests; no initializer or network executes."""
import hashlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from owned_fixture import FixtureDirectory
import validate_public_delivery as delivery


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureDirectory()
        self.addCleanup(self.fixture.cleanup)
        self.root = Path(self.fixture.name)

    def test_download_uses_public_url_and_exact_inspected_bytes(self):
        content = b'inspected bytes'
        record = {'size':len(content),'sha256':hashlib.sha256(content).hexdigest()}
        session = delivery.PublicDelivery(self.root/'diagnostics')
        base = 'https://github.com/orbyss-io/program-kit/releases/download/v1.0.0/'
        with patch.object(delivery.urllib.request,'urlopen',return_value=io.BytesIO(content)) as request:
            session.download(base+'package.zip',self.root/'package.zip',record)
            self.assertEqual(base+'package.zip',request.call_args.args[0])
            self.assertEqual(content,(self.root/'package.zip').read_bytes())
        with patch.object(delivery.urllib.request,'urlopen',return_value=io.BytesIO(b'altered')):
            with self.assertRaisesRegex(ValueError,'differs from inspected'): session.download(base+'package.zip',self.root/'bad.zip',record)
        self.assertFalse((self.root/'bad.zip').exists())
        with patch.object(delivery.urllib.request,'urlopen') as request:
            with self.assertRaises(ValueError): session.download('https://other.example/package.zip',self.root/'bad.zip',record)
            request.assert_not_called()

    def test_journey_invokes_downloaded_initializer_and_documented_updater(self):
        commands, downloads = [], []
        session = SimpleNamespace(run=lambda name,command,cwd:commands.append((name,list(map(str,command)),cwd)),
                                  download=lambda url,path,record:downloads.append((url,path,record)))
        assets = [{'name':'Initialize-ProgramKit-1.0.0.sh','sha256':'a'*64,'size':10},
                  {'name':'program-kit-tooling-1.0.0.zip','sha256':'b'*64,'size':20}]
        promotion = {'source':{'version':'1.0.0'},'assets':assets}
        with patch.object(delivery,'installed_versions',side_effect=[{'all':'1.0.0'},{'all':'0.9.0'},{'all':'1.0.0'}]), patch.object(delivery,'replace_catalogs') as catalogs, patch.object(delivery,'extract'):
            delivery.journey(session,self.root,promotion,'v0.9.0')
        initializer = next(command for name,command,_ in commands if name=='public-initializer')
        upgrade = next(command for name,command,_ in commands if name=='public-upgrade')
        self.assertEqual('bash',initializer[0])
        self.assertEqual(str(downloads[0][1]),initializer[1])
        self.assertTrue(upgrade[1].endswith('public downloaded release/scripts/upgrade_program_kit.py') or upgrade[1].endswith('public downloaded release\\scripts\\upgrade_program_kit.py'))
        self.assertNotIn('--offline',upgrade)
        self.assertEqual(assets,[record for _,_,record in downloads])
        self.assertTrue(downloads[-1][0].endswith('/program-kit-tooling-1.0.0.zip'))
        self.assertTrue(catalogs.call_args.args[1].endswith('/v0.9.0/catalogs'))
        names = [name for name, _, _ in commands]
        preparation = ['prepare-prior-utf8', 'prepare-prior-schema', 'record-prior-schema',
                       'check-prior-schema', 'prior-installation-check']
        self.assertEqual(preparation, names[names.index('install-prior-bundle') + 1:names.index('install-prior-bundle') + 6])
        self.assertLess(names.index('prior-installation-check'), names.index('public-upgrade'))
        prior = self.root / 'public prior consumer'
        for name in preparation:
            _, command, cwd = next(row for row in commands if row[0] == name)
            self.assertEqual(prior, cwd)
            self.assertEqual(str(prior / '.specify/extensions/program-kit-governance/scripts'), str(Path(command[1]).parent))
        self.assertEqual(['--target', '.'], next(command for name, command, _ in commands if name == preparation[0])[2:])
        self.assertEqual(['setup', 'record-copy', 'check-copy'],
                         [next(command for name, command, _ in commands if name == operation)[-1] for operation in preparation[1:4]])

    def test_failed_prior_preparation_never_reaches_updater(self):
        commands = []
        def execute(name, command, cwd):
            commands.append(name)
            if name == 'check-prior-schema':
                raise ValueError('SCHEMA_TOOLS_LOCALLY_EDITED')
        session = SimpleNamespace(run=execute, download=lambda *args: None)
        promotion = {'source': {'version': '1.0.0'}, 'assets': [
            {'name': 'Initialize-ProgramKit-1.0.0.sh'}, {'name': 'program-kit-tooling-1.0.0.zip'}]}
        with patch.object(delivery, 'installed_versions', side_effect=[{'all': '1.0.0'}, {'all': '0.9.0'}]), \
                patch.object(delivery, 'replace_catalogs'):
            with self.assertRaisesRegex(ValueError, 'LOCALLY_EDITED'):
                delivery.journey(session, self.root, promotion, 'v0.9.0')
        self.assertNotIn('public-upgrade', commands)
        self.assertNotIn('prior-installation-check', commands)

    def test_prior_baseline_uses_latest_published_stable_below_candidate(self):
        releases = [{'tag_name':tag,'draft':draft,'prerelease':pre} for tag,draft,pre in
                    [('v1.0.0',False,False),('v0.9.0',False,False),('v0.8.0',False,False),('v0.9.1',True,False),('v0.9.2',False,True)]]
        self.assertEqual('v0.9.0',delivery.previous_release(releases,'1.0.0'))
        with self.assertRaises(ValueError): delivery.previous_release([], '1.0.0')

    def test_failure_timeout_and_incomplete_cleanup_are_nonpassing(self):
        session = delivery.PublicDelivery(self.root/'diagnostics')
        for changes in ({'exitCode':7},{'timedOut':True},{'cleanupComplete':False},{'logsDrained':False}):
            result = SimpleNamespace(**{'exitCode':0,'timedOut':False,'cleanupComplete':True,'logsDrained':True,**changes})
            with self.subTest(changes=changes), patch.object(delivery,'run_supervised',return_value=result):
                with self.assertRaisesRegex(ValueError,'failed or timed out'): session.run('negative',['fictional'],self.root)
        session.started -= 121
        with self.assertRaisesRegex(ValueError,'budget'): session.remaining()

    def test_shared_supervisor_retains_actual_child_logs(self):
        session = delivery.PublicDelivery(self.root/'diagnostics')
        output = session.run('fictional',[delivery.sys.executable,'-c','print("bounded diagnostic")'],self.root)
        self.assertEqual('bounded diagnostic',output.strip())
        self.assertTrue((session.diagnostics/'fictional/workflow.stdout.log').is_file())


if __name__ == '__main__': unittest.main()
