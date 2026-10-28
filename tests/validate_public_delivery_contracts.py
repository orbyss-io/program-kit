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

    def test_preview_journey_uses_only_exact_tagged_initializer(self):
        commands, downloads = [], []
        session = SimpleNamespace(run=lambda name,command,cwd:commands.append((name,list(map(str,command)),cwd)),
                                  download=lambda url,path,record:downloads.append((url,path,record)))
        asset = {'name':'Initialize-ProgramKit-1.0.0-preview.1.sh','sha256':'a'*64,'size':10}
        promotion = {'source':{'version':'1.0.0-preview.1'},'assets':[asset]}
        with patch.object(delivery,'installed_versions',return_value={'all':'1.0.0-preview.1'}):
            delivery.journey(session,self.root,promotion)
        self.assertEqual(['initialize-git','public-initializer','public-installation-check'], [name for name,_,_ in commands])
        self.assertEqual([asset], [record for _,_,record in downloads])
        self.assertIn('/v1.0.0-preview.1/Initialize-ProgramKit-1.0.0-preview.1.sh', downloads[0][0])
        self.assertEqual(str(downloads[0][1]),commands[1][1][1])

    def test_incoherent_public_installation_is_not_success(self):
        session = SimpleNamespace(run=lambda *args: None, download=lambda *args: None)
        promotion = {'source':{'version':'1.0.0-preview.1'},'assets':[{'name':'Initialize-ProgramKit-1.0.0-preview.1.sh'}]}
        with patch.object(delivery,'installed_versions',return_value={'one':'0.14.3'}), self.assertRaisesRegex(ValueError,'incoherent'):
            delivery.journey(session,self.root,promotion)

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
