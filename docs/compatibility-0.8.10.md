# Program Kit 0.8.10 compatibility report

0.8.10 is a corrective release for existing-installation upgrades. It does not change application
runtime contracts introduced by 0.8.9.

The supported upgrade interface is now the `scripts/upgrade_program_kit.py` file inside the verified
full Program Kit release archive. The earlier remote `specify workflow update` followed by
`specify bundle update` sequence is withdrawn: network transport can fail inside Codex Desktop on
Windows, and a successful bundle operation is not proof that existing component content advanced.

The updater requires an existing Program Kit bundle record. Fresh repositories continue to use the
platform initializer. Existing managed .NET repositories are resynchronized automatically using the
already recorded web and persistence profiles; normal managed-file conflict behavior remains
fail-closed.

Installation validation now includes the preset manifest and registry, bundle preset record, and an
existing `.program-kit/managed.json` version. A consumer with a mixed or partially upgraded state
will stop until it runs the updater from one coherent release source. This is intentionally stricter
than 0.8.9.

Approved bootstrap decisions remain immutable when the installed Program Kit advances. After all
components converge, the updater records explicit Accepted upgrade authority in
`.specify/governance/program-kit-upgrades.json`, bound to the exact bootstrap-decision SHA-256. A
later installed-version mismatch is accepted only when that record names both the original profile
version and the current coherent installed version. Editing the approved bootstrap decision register
is neither required nor permitted.

The governance extension now registers a mandatory `after_constitution` hook. A standalone core
`speckit.constitution` run therefore validates the resulting draft and regenerates the hash-current
constitution review packet before ratification, matching the bootstrap workflow's existing order.
