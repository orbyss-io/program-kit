"""Disposable full-tree fixtures with exact ownership and Windows long-path I/O."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
from owned_scratch import owned_scratch, filesystem_path, native_path


class FixtureDirectory:
    """TemporaryDirectory-shaped adapter; prefix never changes deletion authority."""
    def __init__(self, prefix='', native=False):
        self.owner = owned_scratch(ROOT, 'validation-fixture')
        path = self.owner.__enter__()
        self.name = native_path(path) if native else filesystem_path(path)
        self.closed = False

    def __enter__(self):
        return self.name

    def cleanup(self):
        if not self.closed:
            self.owner.__exit__(None, None, None)
            self.closed = True

    def __exit__(self, kind, error, traceback):
        self.closed = True
        return self.owner.__exit__(kind, error, traceback)
