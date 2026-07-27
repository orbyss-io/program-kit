# .agents

`.agents/` contains canonical, provider-neutral definitions used by a human-led
AI development session, plus reusable tools when explicitly approved.

Capabilities use `.agents/capabilities/<capability-id>/CAPABILITY.md`.
Capability and tool files are the sole editable procedure definitions and
logic. These definitions are development tooling, not Program Kit runtime
inputs; runtime libraries and generated applications must never load or
execute this folder.

See [capabilities/INDEX.md](capabilities/INDEX.md) for the capability registry and availability authority.
