from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Run bounded Program Kit pre-host development prerequisites.")
    parser.add_argument("--docker-command", default=os.environ.get("PROGRAMKIT_DOCKER_COMMAND", "docker"))
    parser.add_argument("--timeout-seconds", type=float, default=float(os.environ.get("PROGRAMKIT_PREFLIGHT_TIMEOUT_SECONDS", "5")))
    parser.add_argument('--require-linux-compose', action='store_true', help='Verify the executable composition backend before dependent behavior.')
    args = parser.parse_args()
    if not 0.1 <= args.timeout_seconds <= 60:
        print("PKP001 preflight timeout must be between 0.1 and 60 seconds.", file=sys.stderr)
        return 1
    command = shutil.which(args.docker_command)
    if command is None:
        print("PKP002 Docker CLI is required for the selected local profile; install it or correct PROGRAMKIT_DOCKER_COMMAND.", file=sys.stderr)
        return 2
    try:
        result = subprocess.run(
            [command, "info", "--format", "{{json .ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"PKP003 Docker daemon did not answer within the Program Kit preflight budget ({args.timeout_seconds:g}s).", file=sys.stderr)
        return 3
    if result.returncode != 0:
        print("PKP004 Docker CLI is installed, but the daemon is unavailable; start Docker and retry.", file=sys.stderr)
        return 4
    try:
        version = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        version = "resolved"
    safe_version = version if isinstance(version, str) and len(version) <= 32 else "resolved"
    if args.require_linux_compose:
        try:
            platform = subprocess.run([command, 'info', '--format', '{{json .OSType}}'], capture_output=True,
                                      text=True, timeout=args.timeout_seconds, check=False)
            compose = subprocess.run([command, 'compose', 'version', '--short'], capture_output=True,
                                     text=True, timeout=args.timeout_seconds, check=False)
        except (OSError, subprocess.TimeoutExpired):
            print('PKP005 Docker Linux/Compose capability probe failed before preparation. Verify Docker Desktop in the user terminal.', file=sys.stderr)
            return 5
        try:
            operating_system = json.loads(platform.stdout.strip())
        except json.JSONDecodeError:
            operating_system = None
        if platform.returncode or operating_system != 'linux':
            print('PKP006 selected foundation images require a working Linux-container Docker engine. Switch Docker Desktop to Linux containers, verify docker info, then retry.', file=sys.stderr)
            return 6
        match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9_.-]+)?', compose.stdout.strip())
        if compose.returncode or not match or tuple(map(int, match.groups())) < (2, 24, 0):
            print('PKP007 composition requires Docker Compose 2.24.0 or newer. Verify docker compose version in the user terminal before preparation.', file=sys.stderr)
            return 7
    print(f"Docker CLI and daemon ready (server version {safe_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
