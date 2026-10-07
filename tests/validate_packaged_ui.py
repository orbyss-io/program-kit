from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    package = root / "artifacts" / f"program-kit-governance-{version}.zip"
    with tempfile.TemporaryDirectory(prefix="program-kit-packaged-ui-") as temporary:
        consumer = Path(temporary) / "consumer"
        consumer.mkdir()
        installed = consumer / ".specify/extensions/program-kit-governance"
        with zipfile.ZipFile(package) as archive:
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or ".." in path.parts or "\\" in member.filename or ":" in member.filename:
                    raise AssertionError("Unsafe packaged path")
            archive.extractall(installed)
        for action in ("init", "validate", "build", "check", "explain"):
            result = subprocess.run([sys.executable, str(installed / "scripts/ui_profile.py"), action, "--target", str(consumer)],
                                    cwd=consumer, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise AssertionError(f"Packaged UI {action} failed: {result.stdout}\n{result.stderr}")
            if action == 'explain':
                assert json.loads(result.stdout)['presentation'] == 'modern-product-v1'
        output = consumer / "web/generated/program-kit"
        resources = json.loads((output / "publication.json").read_text())["resources"]
        assert not any(resource["route"] == "/account" for resource in resources)
        assert (output / "acceptance/tests/package-lock.json").is_file()
        assert (output / "public/assets/icons/LICENSE.txt").is_file()
        assert (output / "integration/tokens.json").is_file()
        assert (output / 'integration/auth/logout-error.html').is_file()
        assert 'parent=keycloak' in (output / 'integration/auth/keycloak/login/theme.properties').read_text()
        assert not any('/auth/' in resource['file'] for resource in resources)
        # Archived consumers with no new selection keep the old visual presentation after rebuild.
        profile_path = consumer / '.program-kit/ui/profile.json'
        profile = json.loads(profile_path.read_text())
        profile.pop('presentation')
        profile_path.write_text(json.dumps(profile), encoding='utf-8')
        for action in ('build', 'check'):
            result = subprocess.run([sys.executable, str(installed/'scripts/ui_profile.py'), action, '--target', str(consumer)],
                                    cwd=consumer, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stderr
        assert not (output/'integration/auth/logout-error.html').exists()
        assert '--pk-motion-enter' not in (output/'public/assets/tokens.css').read_text()
    print("Packaged UI modern init/validate/build/check/explain and classic compatibility passed without repository imports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
