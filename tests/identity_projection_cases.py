"""Identity authority and preserved local-repair sync cases in disposable roots."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from owned_fixture import FixtureDirectory


def exercise(root):
    sys.path.insert(0, str(root / 'extensions/program-kit-dotnet/scripts'))
    import identity_fixture
    template = root / 'extensions/program-kit-dotnet/templates/dotnet'
    compose = (template / 'web-profiles/common/deploy/compose.identity.yml').read_bytes()
    image = identity_fixture.provider_image(compose)
    for invalid in (image.split('@')[0], image.replace('sha256:', 'sha512:'), image + '\nimage: ' + image):
        try:
            identity_fixture.provider_image(('image: ' + invalid).encode())
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid or ambiguous identity image authority accepted')
    replacement = 'quay.io/keycloak/keycloak:99.0.1@sha256:' + 'a' * 64
    for profile in ('bff-cookie', 'spa-pkce'):
        projected = json.loads(identity_fixture.render_provider_profile(
            (template / f'web-profiles/{profile}/eng/web-profile.json').read_bytes(), replacement))
        assert projected['localIdentityProvider'] == 'keycloak-99.0.1'
        assert projected['localIdentityProviderImage'] == replacement
    with FixtureDirectory(prefix='identity-local-repair-') as directory:
        fixture = Path(directory)
        sources = fixture / 'source'
        shutil.copytree(root / 'extensions', sources / 'extensions', ignore=shutil.ignore_patterns('__pycache__', 'bin', 'obj', 'node_modules'))
        copied = sources / 'extensions/program-kit-dotnet'
        wrapper = copied / 'templates/dotnet/files/eng/Invoke-RepositoryVerification.ps1'
        wrapper.write_bytes(wrapper.read_bytes() + b'\n# Retained local isolation repair\n')
        consumer = fixture / 'consumer'
        command = [sys.executable, str(copied / 'scripts/dotnet_sync.py'), '--target', str(consumer),
                   '--profile-selected', '--foundation-host-accepted', '--building-block-sources-approved',
                   '--web-profile', 'bff-cookie']
        installed = subprocess.run(command, capture_output=True, text=True)
        assert installed.returncode == 0, installed.stdout + installed.stderr
        # Fresh consumers must receive the transitive helpers used by their public
        # engineering entry points; source-tree imports cannot establish this.
        inspected = subprocess.run([sys.executable, '-E', '-s', '-S', str(consumer/'eng/retained_inputs.py'),
                                   'inspect', '--repository', str(consumer)], capture_output=True, text=True)
        assert inspected.returncode == 0, inspected.stdout + inspected.stderr
        assert json.loads(inspected.stdout)['configured'] is False
        assert (consumer/'eng/toolkit_verification.py').is_file()
        assert (consumer/'eng/source_quality.py').is_file()
        module = consumer / 'eng/ProviderTestEnvironment.psm1'
        module.write_text('# Consumer-owned isolation module preserved by sync\n')
        module_bytes = module.read_bytes()
        # Reconcile the source template first. Actual sync writes and records the
        # accepted consumer repair; no generated-state hash is patched by this test.
        wrapper.write_bytes((root / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/Invoke-RepositoryVerification.ps1').read_bytes())
        preview = subprocess.run(command + ['--check'], capture_output=True, text=True)
        assert preview.returncode == 1 and 'conflicts: 0' in preview.stdout, preview.stdout + preview.stderr
        applied = subprocess.run(command, capture_output=True, text=True)
        assert applied.returncode == 0, applied.stdout + applied.stderr
        converged = subprocess.run(command + ['--check'], capture_output=True, text=True)
        assert converged.returncode == 0, converged.stdout + converged.stderr
        assert module.read_bytes() == module_bytes
        descriptor = json.loads((consumer / 'eng/web-profile.json').read_text())
        assert descriptor['localIdentityProviderImage'] == identity_fixture.provider_image((consumer / 'deploy/compose.identity.yml').read_bytes())
        current = consumer / 'eng/Invoke-RepositoryVerification.ps1'
        current.write_bytes(current.read_bytes() + b'\n# Unreviewed conflicting consumer edit\n')
        before = {p.relative_to(consumer): p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
        conflict = subprocess.run(command, capture_output=True, text=True)
        assert conflict.returncode == 2 and 'Invoke-RepositoryVerification.ps1' in conflict.stdout, conflict.stdout + conflict.stderr
        assert before == {p.relative_to(consumer): p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
    print('Identity authority projection, repaired-template convergence and genuine conflict preservation passed.')
