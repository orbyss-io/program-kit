"""Compatibility entrypoint for the standalone engineering verifier."""
import sys
from pathlib import Path
_engine = Path(__file__).resolve().parents[2] / 'program-kit-dotnet/templates/dotnet/files/eng'
sys.path.insert(0, str(_engine))
from repository_architecture import *
if __name__ == '__main__':
    raise SystemExit(main())
