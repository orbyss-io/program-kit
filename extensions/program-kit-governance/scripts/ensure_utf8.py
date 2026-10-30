from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


CONTENT = '''"""Program Kit UTF-8 bootstrap for Spec Kit Python entry points."""
from __future__ import annotations

import sys

for _program_kit_stream in (sys.stdout, sys.stderr):
    _program_kit_reconfigure = getattr(_program_kit_stream, "reconfigure", None)
    if callable(_program_kit_reconfigure):
        _program_kit_reconfigure(encoding="utf-8", errors="backslashreplace")
'''
MARKER = "# PROGRAM-KIT:UTF8-ENTRYPOINT"
ENTRYPOINT_BOOTSTRAP = '''# PROGRAM-KIT:UTF8-ENTRYPOINT
import sys as _program_kit_sys
for _program_kit_stream in (_program_kit_sys.stdout, _program_kit_sys.stderr):
    _program_kit_reconfigure = getattr(_program_kit_stream, "reconfigure", None)
    if callable(_program_kit_reconfigure):
        _program_kit_reconfigure(encoding="utf-8", errors="backslashreplace")

'''


def hardened(content: str) -> str:
    normalized = content.replace("\r\n", "\n")
    if MARKER in normalized:
        if normalized.count(ENTRYPOINT_BOOTSTRAP) != 1:
            raise ValueError('PKU001 unknown UTF-8 entrypoint customization; preserve and reconcile it')
        return normalized
    lines = normalized.splitlines(keepends=True)
    future_indexes = [index for index, line in enumerate(lines) if line.startswith("from __future__ import ")]
    insert_at = max(future_indexes) + 1 if future_indexes else 0
    lines.insert(insert_at, ENTRYPOINT_BOOTSTRAP)
    return "".join(lines)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def transformation_plan(root):
    """Prove the exact reversible transform; never re-sign the native manifest.

    This establishes consistency with the supplied native manifest. Authenticating
    that manifest against the selected public distribution is a separate check.
    """
    manifest_path = root / '.specify/integrations/speckit.manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get('integration') != 'speckit' or not isinstance(manifest.get('files'), dict):
        raise ValueError('PKU001 a current native core manifest is required before UTF-8 reconciliation')
    prefix = '.specify/scripts/python/'
    changes, files = {}, {}
    for relative, expected in sorted(manifest['files'].items()):
        if not relative.startswith(prefix) or not relative.endswith('.py'):
            continue
        if Path(relative).parent.as_posix() != prefix.rstrip('/'):
            raise ValueError('PKU001 unsafe core entrypoint path')
        target = root / relative
        if (not target.resolve().is_relative_to(root.resolve()) or any(
                part.is_symlink() or getattr(part, 'is_junction', lambda: False)()
                for part in (target, *target.parents) if part.is_relative_to(root))):
            raise ValueError('PKU001 linked core entrypoint requires explicit reconciliation: ' + relative)
        actual = target.read_bytes()
        source = actual
        if digest(actual) != expected:
            content = actual.decode('utf-8')
            if content.count(ENTRYPOINT_BOOTSTRAP) != 1:
                raise ValueError('PKU001 unexplained core integrity discrepancy: ' + relative)
            source = content.replace(ENTRYPOINT_BOOTSTRAP, '', 1).encode('utf-8')
            if digest(source) != expected or hardened(source.decode('utf-8')).encode('utf-8') != actual:
                raise ValueError('PKU001 core edit is not the exact owned UTF-8 transformation: ' + relative)
        transformed = hardened(source.decode('utf-8')).encode('utf-8')
        # Native generation uses LF. Refuse an unreproducible newline transform
        # rather than manufacturing a source witness for different original bytes.
        if transformed.replace(ENTRYPOINT_BOOTSTRAP.encode(), b'', 1) != source:
            raise ValueError('PKU001 core source requires native LF regeneration before UTF-8 transformation: ' + relative)
        files[relative] = {'nativeSha256': expected, 'transformedSha256': digest(transformed)}
        if transformed != actual:
            changes[target] = transformed
    if not files:
        raise ValueError('PKU001 native core manifest contains no Python entrypoints')
    record = {'schemaVersion': 1, 'kind': 'core-utf8-transformation', 'nativeVersion': manifest.get('version'),
              'nativeManifestSha256': digest(manifest_bytes), 'recipeSha256': digest(ENTRYPOINT_BOOTSTRAP.encode()),
              'scope': 'exact reversible transformation; public manifest authentication remains required', 'files': files}
    return changes, record


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.utf8-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Install idempotent UTF-8 startup for Spec Kit Python scripts.")
    parser.add_argument("--target", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.target).resolve()
    destination = root / ".specify" / "scripts" / "python" / "sitecustomize.py"
    record_path = root / 'config/program-kit/core-utf8-transformation.json'
    desired = CONTENT.replace("\r\n", "\n")
    current = destination.read_text(encoding="utf-8") if destination.is_file() else None
    try:
        changes, record = transformation_plan(root)
        record_bytes = (json.dumps(record, sort_keys=True, indent=2) + '\n').encode('utf-8')
        if current is not None and current != desired:
            raise ValueError('PKU001 customized sitecustomize.py requires explicit reconciliation')
        if destination.is_symlink() or record_path.is_symlink() or record_path.parent.is_symlink() or getattr(record_path.parent, 'is_junction', lambda: False)():
            raise ValueError('PKU001 linked UTF-8 bookkeeping requires explicit reconciliation')
        current_record = record_path.read_bytes() if record_path.is_file() else None
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if current == desired and not changes and current_record == record_bytes:
        print("Spec Kit Python UTF-8 startup is current")
        return 0
    if args.check:
        print(f"PKU001 Spec Kit Python UTF-8 startup is missing or stale: {destination}", file=sys.stderr)
        return 1
    for path, content in changes.items():
        atomic_write(path, content)
    atomic_write(destination, desired.encode('utf-8'))
    atomic_write(record_path, record_bytes)
    print(f"installed Spec Kit Python UTF-8 startup and reconciled {len(record['files'])} manifest-bound entrypoints: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
