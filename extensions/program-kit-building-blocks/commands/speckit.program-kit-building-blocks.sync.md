---
description: Plan, check, or apply an explicitly selected managed building-block composition.
scripts:
  py: scripts/building_blocks.py
---

# Building-block synchronization

Use this helper when the user chooses Program Kit's managed composition tooling.
Knowledge and native Spec Kit phases do not require it. Research and document local
alternatives when needed; an unlisted choice need not become a supported recipe first.

1. Use `draft --capability <id>` to suggest compositions. Complete the scopes,
   actual target paths, instances, bindings and options with the user. Include only
   capabilities needed by this product. Review technology and ownership decisions
   before accepting the selection.
2. Cite existing Accepted decisions from the domain/C4 map with
   `accept --decision-id <id> --rationale <text>`. The minimal map uses readable
   decision documents; accepting a selection does not rewrite that map or create
   approval fingerprints. Human review happens in the conversation.
3. Run `plan` and inspect the concrete managed changes and ownership. Run `apply`
   with that plan's exact `planDigest` to protect against changed generator inputs.
4. Restore declared project packages and run relevant native builds and tests.
   Existing restore helpers support exact lock renewal and locked validation.
   Agents may restore project packages using installed tools. If a required device
   tool is missing or incompatible, explain the blocked operation and present a
   platform-appropriate preparation script for the human to run.

`plan` and `check` are read-only. `apply` preserves consumer-owned entries and uses
a recoverable transaction; use `recover` after an interrupted write. It does not
choose architecture or establish consent. Keep credentials and deployment secrets
out of selections, generated locks, command arguments and logs.

The bundled profile supplies qualified default package pins. An explicit profile
or catalog selects different inputs; supported-recipe qualification describes
maintainer evidence, not permission to make informed local choices. Changing a
dependency is a separate reviewed engineering change. Review affected manifests,
configuration and behavior, preserve native lock files, and run relevant tests.
Installing or updating Program Kit does not silently advance application packages.

Native SDK evaluation and actual package/output ownership remain authoritative
for this generator's supported project shapes. If a custom graph or relocated
output is unsupported, explain that limit and use native project tooling or add
a suitable adapter. Do not invent successful restoration or compatibility proof.
