---
description: Prepare a delivery profile and repository binding without changing authority.
scripts:
  py: scripts/delivery.py
---

Read `.specify/extensions/program-kit-delivery/references/delivery.md` and the selected provider
default JSON in that references directory. Explain that installation is
disabled by default and preparation does not activate cloud authority. Ask only for unknown
consumer choices; preserve already accepted decisions. Run `{SCRIPT} status` first.

Keep the shared profile in consumer Git. It owns field/type/state semantics, role policy and
coordination rules. Replace proposed identity/location placeholders through intake; never claim
they identify verified platform resources. Pin an already committed profile with repository ID,
commit, path and exact-byte SHA-256 in the binding; its local snapshot must match those bytes.
Do not put a profile's own commit hash inside its payload. No credentials belong in these files.

Prepare a reviewable candidate binding and run `{SCRIPT} validate-profile --input <profile>`.
After the user's configuration choices are settled, run `{SCRIPT} prepare --input <binding>`.
The command writes only checked-in local preparation records. Report that provider activation
and connection verification are unavailable in Phase 1. Never invent an activation receipt,
modify history to disable delivery, or invoke the contributor Phase 0 live probes on a consumer.

Machine-local governance settings cannot override delivery authority. Preserve missing or
inconsistent connected records for recovery. Changing a profile after activation and deliberate
disconnection require their later reviewed operations; installation or an upgrade is neither.
