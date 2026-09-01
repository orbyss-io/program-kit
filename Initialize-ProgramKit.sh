#!/usr/bin/env bash
set -euo pipefail

PROGRAM_KIT_REF="v0.6.5"

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

has_program_kit_catalog() {
  local catalog_config
  for catalog_config in \
    ".specify/extension-catalogs.yml" \
    ".specify/preset-catalogs.yml" \
    ".specify/workflow-catalogs.yml" \
    ".specify/bundle-catalogs.yml"; do
    if [[ -f "$catalog_config" ]] && grep -q 'program-kit' "$catalog_config"; then
      return 0
    fi
  done
  return 1
}

if {
  [[ -f ".specify/bundle-records.json" ]] &&
    grep -Eq '"bundle_id"[[:space:]]*:[[:space:]]*"program-kit"' ".specify/bundle-records.json"
} || {
  [[ -f ".specify/extensions.yml" ]] &&
    grep -Eq 'program-kit-(governance|dotnet)' ".specify/extensions.yml"
} || {
  [[ -f ".specify/workflows/workflow-registry.json" ]] &&
    grep -q 'program-kit-bootstrap' ".specify/workflows/workflow-registry.json"
} || has_program_kit_catalog \
  || [[ -f ".specify/extensions/program-kit-governance/extension.yml" ]] \
  || [[ -f ".specify/extensions/program-kit-dotnet/extension.yml" ]] \
  || [[ -f ".specify/workflows/program-kit-bootstrap/workflow.yml" ]] \
  || [[ -f ".agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md" ]]; then
  printf 'ERROR: Program Kit is already installed, or a partial Program Kit installation exists in %s.\n' "$current_root" >&2
  printf 'Use the documented Program Kit update commands instead of running the initializer again.\n' >&2
  exit 2
fi

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

printf '\nProgram Kit initialization is complete.\n'
