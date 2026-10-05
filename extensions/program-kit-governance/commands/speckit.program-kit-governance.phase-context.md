---
description: Supply applicable architecture and coding guidance before work.
scripts:
  py: scripts/phase_obligations.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} project --feature-dir <feature> --phase planning`
before planning, `--phase after-plan` before tasks, and `--phase implementation` before coding.
Read the selected reference sections. Apply their conditions to concrete design/code choices;
record decisions, exceptions and actual required tests in the existing plan and tasks.
Use the project's analyzers and targeted tests during implementation. Do not create phase-context,
obligation-design/review, semantic-contract or proof-attestation files. No renewed human approval
is needed for generated context, changed toolkit bytes or test execution.
