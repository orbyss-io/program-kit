"""Build concise current release guidance; published 0.x history is immutable source data."""
from pathlib import Path
from product_version import parse, is_preview


def build(root, destination, version, *, aggregates=True):
    root, destination = Path(root), Path(destination)
    parse(version)
    destination.mkdir(parents=True, exist_ok=True)
    notes = (root / 'releases/preview.md').read_bytes().replace(b'\r\n', b'\n')
    (destination / 'RELEASE-NOTES.md').write_bytes(notes)
    channel = 'a preview selected explicitly by its tag' if is_preview(version) else 'a stable release'
    (destination / 'COMPATIBILITY.md').write_text(
        '# Compatibility\n\nProgram Kit ' + version + ' is ' + channel + '.\n\n'
        '0.x consumers re-onboard in a fresh checkout. Keep the original repository and use its authored '
        'architecture, ADRs and product documents as intake inputs. No workflow authority is translated.\n\n'
        'Later toolkit updates preserve authored application/specification work and locks. '
        'The updater refuses unknown or customized toolkit bytes; reconcile their owner explicitly. '
        'A toolkit update does not migrate application dependencies or establish product acceptance.\n', encoding='utf-8')
    return destination
