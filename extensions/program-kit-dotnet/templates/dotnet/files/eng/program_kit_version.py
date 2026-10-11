"""Source-template authority; sync renders the installed extension's exact version."""
from pathlib import Path
import re


def source_version():
    for parent in Path(__file__).resolve().parents:
        extension = parent / 'extension.yml'
        if extension.is_file():
            text = extension.read_text(encoding='utf-8')
            if re.search(r'^\s*id:\s*"program-kit-dotnet"\s*$', text, re.MULTILINE):
                match = re.search(r'^\s*version:\s*"([^"]+)"\s*$', text, re.MULTILINE)
                if match:
                    return match[1]
    raise ValueError('Program Kit version authority is absent; synchronize the installed baseline')


PROGRAM_KIT_VERSION = source_version()
