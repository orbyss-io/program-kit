#!/usr/bin/env bash
set -Eeuo pipefail

PROGRAM_KIT_REF="v0.12.11"
program_kit_stage="prerequisite checks"
trap 'status=$?; printf "ERROR: Program Kit initialization stopped during %s with exit code %s. Preserve the output and partial installation for diagnosis.\n" "$program_kit_stage" "$status" >&2; exit "$status"' ERR

# Run from a normal user-owned Bash shell in Linux, macOS, or WSL.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
current_root="$(pwd -P)"
script_name="$(basename -- "${BASH_SOURCE[0]}")"

if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9_-]+$ ]]; then
  printf 'ERROR: Supply exactly one Spec Kit integration ID, for example: %s codex\n' "$script_name" >&2
  exit 2
fi
program_kit_integration="$1"

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
  printf 'PKT030: Spec Kit >=1.1.1,<2 required by the bundle; detected=missing executable=missing. In your own terminal: uv tool install specify-cli==1.1.1 --force --no-python-downloads; uv tool update-shell. Refresh and verify command -v specify and specify version. If already installed, repair persistent PATH. For missing uv: https://docs.astral.sh/uv/getting-started/installation/\n' >&2
  exit 2
fi
if ! specify_version="$(specify --version)"; then
  printf 'ERROR: The specify command was found but could not execute successfully. Repair Spec Kit and rerun the initializer.\n' >&2
  exit 2
fi
printf '%s\n' "$specify_version"
if [[ ! "$specify_version" =~ ^specify\ 1\.([0-9]+)\.([0-9]+)$ ]] \
  || (( 10#${BASH_REMATCH[1]} < 1 )) \
  || (( 10#${BASH_REMATCH[1]} == 1 && 10#${BASH_REMATCH[2]} < 1 )); then
  printf 'ERROR: Spec Kit >=1.1.1,<2 is required; selected version: %s\n' "$specify_version" >&2
  exit 2
fi
if ! command -v git >/dev/null 2>&1; then
  printf 'ERROR: Git must be available as git because coding-agent workflows run inside a Git work tree.\n' >&2
  exit 2
fi
if ! git --version; then
  printf 'ERROR: The git command was found but could not execute successfully. Repair Git and rerun the initializer.\n' >&2
  exit 2
fi
if ! git rev-parse --is-inside-work-tree; then
  printf 'ERROR: This directory is not inside an initialized Git work tree.\n' >&2
  printf 'Run these commands from %s, then rerun %s %s:\n\n' "$current_root" "$script_name" "$program_kit_integration" >&2
  printf '  git init\n' >&2
  printf '  git status\n' >&2
  exit 2
fi
if [[ -z "${SPECKIT_PYTHON:-}" ]]; then
  if ! command -v python >/dev/null 2>&1; then
    printf 'PKT030: Python >=3.11 required by the Spec Kit runtime; detected=missing executable=missing. In your own terminal: uv python install 3.11 --default; uv python update-shell, or retain your existing device installer. Refresh and verify command -v python and python --version. Missing uv: https://docs.astral.sh/uv/getting-started/installation/\n' >&2
    exit 2
  fi
  if ! SPECKIT_PYTHON="$(python -c 'import sys; print(sys.executable)')"; then
    printf 'ERROR: Cannot resolve the Python interpreter.\n' >&2
    exit 2
  fi
fi
export SPECKIT_PYTHON
if ! "$SPECKIT_PYTHON" -c 'import sys; assert sys.version_info >= (3,11)' >/dev/null 2>&1; then
  printf 'ERROR: The selected Python interpreter must support Python >=3.11.\n' >&2
  exit 2
fi
program_kit_stage="read-only shared device readiness"
"$SPECKIT_PYTHON" -c 'import sys; print(sys.executable); assert sys.version_info >= (3,11), "Python >=3.11 is required; update shared device Python in your own terminal and refresh the session"'
if [[ -f "$script_dir/scripts/initialize_device.py" ]]; then
  "$SPECKIT_PYTHON" "$script_dir/scripts/initialize_device.py" --ref "$PROGRAM_KIT_REF" --project-root "$current_root" --release-root "$script_dir"
else
  program_kit_device_preflight="$(mktemp "${TMPDIR:-/tmp}/program-kit-device.XXXXXX")"
  "$SPECKIT_PYTHON" -c 'import sys,urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])' \
    "https://raw.githubusercontent.com/orbyss-io/program-kit/$PROGRAM_KIT_REF/scripts/initialize_device.py" "$program_kit_device_preflight"
  "$SPECKIT_PYTHON" "$program_kit_device_preflight" --ref "$PROGRAM_KIT_REF" --project-root "$current_root"
fi

if ! "$SPECKIT_PYTHON" -c 'import yaml' >/dev/null 2>&1; then
  if ! "$SPECKIT_PYTHON" -m pip --version >/dev/null 2>&1; then
    printf 'ERROR: PyYAML is missing and python -m pip is unavailable. Install pip for this Python interpreter, then install PyYAML>=6,<7 and rerun the initializer.\n' >&2
    exit 2
  fi
  printf 'Installing the PyYAML dependency required by the Spec Kit Python resolver...\n'
  if ! "$SPECKIT_PYTHON" -m pip install --disable-pip-version-check 'PyYAML>=6,<7'; then
    printf 'ERROR: PyYAML could not be installed for the python command. Install PyYAML>=6,<7 for that interpreter and rerun the initializer.\n' >&2
    exit 2
  fi
  if ! "$SPECKIT_PYTHON" -c 'import yaml' >/dev/null 2>&1; then
    printf 'ERROR: PyYAML is still unavailable to the python command after installation.\n' >&2
    exit 2
  fi
fi
catalog_root="https://raw.githubusercontent.com/orbyss-io/program-kit/${PROGRAM_KIT_REF}/catalogs"

program_kit_stage="step 1/8"
printf '[1/8] Initializing Spec Kit for %s with the Python script flavor...\n' "$program_kit_integration"
specify init . --force --non-interactive --integration "$program_kit_integration" --script py

program_kit_stage="step 2/8"
printf '[2/8] Registering the Program Kit extension catalog...\n'
specify extension catalog add "${catalog_root}/extensions.json" --name program-kit --install-allowed

program_kit_stage="step 3/8"
printf '[3/8] Registering the Program Kit preset catalog...\n'
specify preset catalog add "${catalog_root}/presets.json" --name program-kit --install-allowed

program_kit_stage="step 4/8"
printf '[4/8] Registering the Program Kit workflow catalog...\n'
specify workflow catalog add "${catalog_root}/workflows.json" --name program-kit

program_kit_stage="step 5/8"
printf '[5/8] Registering the Program Kit bundle catalog...\n'
specify bundle catalog add "${catalog_root}/bundles.json" --id program-kit --policy install-allowed

program_kit_stage="step 6/8"
printf '[6/8] Installing the bootstrap workflow...\n'
specify workflow add program-kit-bootstrap

program_kit_stage="step 7/8"
printf '[7/8] Installing Program Kit...\n'
specify bundle install program-kit --integration "$program_kit_integration"
"$SPECKIT_PYTHON" .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
"$SPECKIT_PYTHON" .specify/extensions/program-kit-governance/scripts/schema_runtime.py setup
"$SPECKIT_PYTHON" .specify/extensions/program-kit-governance/scripts/schema_runtime.py record-copy

program_kit_stage="step 8/8"
printf '[8/8] Switching Program Kit catalogs to the update channel...\n'
specify extension catalog remove program-kit
specify preset catalog remove program-kit
specify workflow catalog remove 0
specify bundle catalog remove program-kit
specify extension catalog add 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/extensions.json' --name program-kit --install-allowed
specify preset catalog add 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/presets.json' --name program-kit --install-allowed
specify workflow catalog add 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/workflows.json' --name program-kit
specify bundle catalog add 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/bundles.json' --id program-kit --policy install-allowed

printf '\nProgram Kit initialization is complete.\n'
