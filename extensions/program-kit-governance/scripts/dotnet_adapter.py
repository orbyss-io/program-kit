"""Locate the co-installed canonical .NET adapter and its engineering modules.

Governance entrypoints must work in a fresh process without consumer eng files or
another command having populated sys.path. No runtime/tool acquisition occurs here.
"""
from pathlib import Path
import sys


def bootstrap():
    extension = Path(__file__).resolve().parents[2] / 'program-kit-dotnet'
    scripts = extension / 'scripts'
    engineering = extension / 'templates/dotnet/files/eng'
    for directory in (scripts, engineering):
        if not directory.is_dir():
            raise ValueError('Program Kit .NET adapter is incomplete: ' + str(directory))
    for directory in (scripts, engineering):
        location = str(directory)
        if location not in sys.path:
            sys.path.insert(0, location)
    return engineering
