#!/usr/bin/env bash
set -euo pipefail

PROGRAM_KIT_REF="v0.6.3"

# Run from a normal user-owned Bash shell in Linux, macOS, or WSL.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
current_root="$(pwd -P)"
script_name="$(basename -- "${BASH_SOURCE[0]}")"

if [[ "$current_root" != "$script_dir" ]]; then
  printf 'ERROR: Change to the repository root containing %s before running it.\n' "$script_name" >&2
  exit 2
fi

if [[ -n "${CODEX_SESSION_ID:-}" || -n "${CODEX_THREAD_ID:-}" || -n "${CODEX_INTERNAL_ORIGINATOR_OVERRIDE:-}" ]]; then
  printf 'ERROR: Run %s yourself from a normal user-owned Bash shell, not from a Codex Desktop task or interactive Codex CLI agent.\n' "$script_name" >&2
  exit 2
fi

shopt -s dotglob nullglob
for entry in *; do
  entry_name="$(basename -- "$entry")"
  if [[ "$entry_name" != ".git" && "$entry_name" != "$script_name" ]]; then
    printf 'ERROR: %s is not empty. Use a new repository containing only .git and %s.\n' "$current_root" "$script_name" >&2
    exit 2
  fi
done
shopt -u dotglob nullglob

if ! command -v specify >/dev/null 2>&1; then
  printf 'ERROR: Spec Kit 1.0.1 or a compatible 1.x specify command is required.\n' >&2
  exit 2
fi
if ! command -v python >/dev/null 2>&1; then
  printf 'ERROR: Python must be available as python because Program Kit uses the Python Spec Kit runtime.\n' >&2
  exit 2
fi

catalog_root="https://raw.githubusercontent.com/orbyss-io/program-kit/${PROGRAM_KIT_REF}/catalogs"

printf '[1/7] Initializing Spec Kit for Codex with the Python script flavor...\n'
specify init . --force --non-interactive --integration codex --script py

printf '[2/7] Registering the Program Kit extension catalog...\n'
specify extension catalog add "${catalog_root}/extensions.json" --name program-kit --install-allowed

printf '[3/7] Registering the Program Kit preset catalog...\n'
specify preset catalog add "${catalog_root}/presets.json" --name program-kit --install-allowed

printf '[4/7] Registering the Program Kit workflow catalog...\n'
specify workflow catalog add "${catalog_root}/workflows.json" --name program-kit

printf '[5/7] Registering the Program Kit bundle catalog...\n'
specify bundle catalog add "${catalog_root}/bundles.json" --id program-kit --policy install-allowed

printf '[6/7] Installing the bootstrap workflow required by Spec Kit 1.0.1...\n'
specify workflow add program-kit-bootstrap

printf '[7/7] Installing Program Kit...\n'
specify bundle install program-kit --integration codex

printf '\nProgram Kit initialization is complete. No initial design was required.\n'
printf 'Create INITIAL_DESIGN.md when ready, then start the bootstrap from this same normal shell:\n\n'
printf '  specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md --input integration=codex\n'
