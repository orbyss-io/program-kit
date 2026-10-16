#!/usr/bin/env bash
set -eu
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if ! python3 "$script_dir/repair_feedback.py" prerequisites; then
  printf '%s\n' 'Follow https://cli.github.com/ for your Linux distribution, macOS Homebrew/installer, or Windows installer. Add the actual install directory to PATH, reopen your shell, then run gh auth login --hostname github.com yourself. No install or login was attempted.'
  exit 1
fi
