"""Copy only hash-bound public HostedPages deployment bytes into the native bundle.

Foundation owns semantic manifest/content admission at activation. This adapter owns
safe deployment paths, exact public inventory, copying and packaging freshness.
"""
import hashlib
import json
from pathlib import Path
import shutil

FEATURE = 'Orbyss.Foundation.Web.HostedPages'


def deployment_path(root: Path, name: str) -> Path:
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or Path(name).is_absolute() or any(part in {'', '.', '..'} for part in name.split('/'))):
        raise ValueError('PKR024 hosted content requires literal local relative paths')
    candidate = root / name
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('PKR024 hosted content escapes deployment root')
    for path in (candidate, *candidate.parents):
        if path.is_symlink() or path.is_junction():
            raise ValueError('PKR024 linked hosted content is not admissible')
        if path == root:
            break
    return candidate


def inventory(root: Path, shells: dict) -> list[dict]:
    files: dict[str, str] = {}
    for shell in shells['CShells']['Shells'].values():
        if FEATURE not in shell['Features'] or shell['Features'][FEATURE] is False:
            continue
        options = shell.get('Configuration', {}).get('Foundation', {}).get('HostedPages', {})
        base = deployment_path(root, options.get('Root', 'hosted-pages'))
        manifest = deployment_path(base, options.get('Manifest', 'manifest.json'))
        data = manifest.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) > 2 * 1024 * 1024 or digest != options.get('ManifestSha256'):
            raise ValueError('PKR024 hosted manifest bound hash/size mismatch; rebuild before staging')
        declaration = json.loads(data)
        if declaration.get('version') != '1' or declaration.get('currentRevision') != options.get('CurrentRevision'):
            raise ValueError('PKR024 hosted manifest revision/version mismatch')
        files[manifest.relative_to(root).as_posix()] = digest
        total = 0
        for revision in declaration['revisions']:
            for asset in revision['assets']:
                if asset.get('visibility') != 'public':
                    raise ValueError('PKR024 only explicitly public assets can enter a hosted bundle')
                path = deployment_path(base, asset['file'])
                if path.suffix.lower() not in {'.js', '.css', '.png', '.woff2'}:
                    raise ValueError('PKR024 unsupported public runtime content')
                if path.stat().st_size > 8 * 1024 * 1024:
                    raise ValueError('PKR024 hosted asset exceeds supported per-file bound')
                total += path.stat().st_size
                if total > 128 * 1024 * 1024:
                    raise ValueError('PKR024 hosted content exceeds supported maximum deployment bound')
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != asset['sha256']:
                    raise ValueError('PKR024 hosted asset changed after manifest preparation')
                name = path.relative_to(root).as_posix()
                if name in files and files[name] != actual:
                    raise ValueError('PKR024 conflicting hosted content identity')
                files[name] = actual
    return [{'file': name, 'sha256': digest} for name, digest in sorted(files.items())]


def stage(repository: Path, output: Path, shells: dict) -> None:
    admitted = inventory(repository, shells)
    for item in admitted:
        destination = deployment_path(output, item['file'])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / item['file'], destination)
    if inventory(output, shells) != admitted:
        raise ValueError('PKR024 hosted bytes changed during staging')
