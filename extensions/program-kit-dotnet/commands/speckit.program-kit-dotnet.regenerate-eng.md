---
description: Restore disposable eng outputs using the consumer's pinned deterministic generator.
---

Run `python "${PWD}/scripts/regenerate_eng.py" --repository "${PWD}"` from the consumer root, using its
already installed interpreter matching `.python-version`. This is the same maintained
entrypoint used by native restore/build and by humans/CI. It needs neither an agent nor
`.agents`/`.specify` after engineering setup.

Report the actual command and result. On missing input, helper, or exact toolkit/runtime
version, stop with its diagnostic. Restore the selected durable input/tool version through
its owner; do not invent defaults, upgrade dependencies, initialize accounts, install device
tools, start applications/services, or reconstruct files with AI. Author scripts in `<consumer-root>/scripts/`,
helper/application tool source in `tools/`, and configuration/selections/provenance in
`config/program-kit/`. `eng/` is ignored and fully disposable. Preserve existing-layout
consumer source; adoption requires an explicitly reviewed migration.
