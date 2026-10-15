"""Exercise real Windows 8.3 spellings without changing physical fixture ownership."""
import os
from pathlib import Path


def short_path(path):
    path = Path(path).resolve()
    if os.name != 'nt':
        return path
    import ctypes
    from ctypes import wintypes
    function = ctypes.windll.kernel32.GetShortPathNameW
    function.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    function.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    length = function(str(path), buffer, len(buffer))
    if not length or length >= len(buffer):
        raise OSError('Owned fixture short-path lookup failed')
    result = Path(buffer.value)
    if not result.samefile(path):
        raise AssertionError('Short spelling changed fixture ownership')
    return result
