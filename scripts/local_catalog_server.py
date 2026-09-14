"""Serve disposable candidate archives on loopback with bounded binary writes."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil


class CatalogHandler(SimpleHTTPRequestHandler):
    def copyfile(self, source, outputfile):
        # Python's Windows default is 1 MiB. Local comparisons observed incomplete
        # transfers with that size; 64 KiB preserves exact bytes and bounds writes.
        shutil.copyfileobj(source, outputfile, length=64 * 1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('port', type=int)
    parser.add_argument('--directory', required=True, type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    if not directory.is_dir():
        parser.error('directory must be a directory')
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(CatalogHandler, directory=str(directory))) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
