---
description: View or preview Program Kit's generated C4/Structurizr workspace projection in a safe localhost viewer. Use when the user asks to view, open, render, preview, or inspect the C4 map, architecture map, Structurizr model, or workspace.dsl, viewing supports informed review without architecture editing or acceptance.
---

## Purpose

Help the human visually inspect the generated C4 projection without changing its semantic source.
Read `references/c4-viewing.md` and the managed profile it names. Treat
`docs/architecture/architecture-map.json` as canonical and `docs/architecture/workspace.dsl` as a
generated, read-only review projection. Never import viewer or DSL changes into the map.

Inspection accepts the actual canonical map and its current generated projection. Small schema2.0
and detailed1.1 maps retain their own model/export contracts. No intake status, source-approval
hash or confirmation receipt is needed. Viewing never edits authored meaning or accepts proposals.

## View workflow

This is a bounded viewing task. Allow at most three minutes of active work from invocation to
the diagram URL or a clear blocker. Read only this command, `references/c4-viewing.md`, and its
managed runtime profile; let the deterministic launcher inspect architecture files. Never print
whole generated artifacts, full server logs, or repository-wide diffs. Run inspection once and
start once with `--detach`; never poll a foreground server from an agent. Stop on the first
validation, startup, workspace-loading, or browser failure and report the concise diagnostic,
preserved evidence path when present, and one actionable next step. Do not repair architecture,
rewrite intake bindings, search for alternate viewers, or restart repeatedly during a view request.
After an explicit user-approved prerequisite repair, a new view attempt may begin with a new budget.

Run the deterministic inspection command from `references/c4-viewing.md`. Report missing files,
invalid JSON/model references or DSL, or a projection that no longer
matches a fresh export. Do not start a viewer until inspection says the projection is current.

If the pinned Docker image is already local, start the viewer with the documented detached command.
If a supported Java runtime and exact pinned WAR are already available, the launcher selects that
fallback. The consumer needs Python plus either running Docker with the pinned local image or
Java 21+ with the pinned local WAR, and a local browser. Missing prerequisites are blockers to
report immediately, never a reason for an open-ended tool search. Open the returned localhost URL
when an available browser tool can do so; otherwise give
the URL clearly. The launcher opens the first diagram directly; tell the human that the left
thumbnail rail switches between generated views and that the diagram key explains the color and
border cues. Explain that a magnifier on an element opens a linked detail view, no magnifier means
the map defines no deeper C4 view, and the `+`/`-` controls zoom the canvas. Include the exact stop
command in the response.

The launcher checks the diagrams page and parsed workspace for the requested view, including when
reusing a session. This establishes availability, not completed visual review. If automatic browser
opening fails, provide the working URL immediately and end the task. When a browser tool is
available, make one bounded attempt to show the diagram and check that the canvas actually renders;
stop with the URL and blocker if it does not. Do not claim the human saw a diagram from HTTP
readiness or a successful browser-launch call alone. If sandbox permissions prevent Docker or
localhost access, use the integration's supported permission mechanism once when authorized;
otherwise report the restriction and the exact command for the user's local terminal, then stop.

If the required local binary/artifact is absent, report the exact prerequisite and provide
user-terminal preparation. The agent must not install device software or retrieve its viewer runtime; do not use an unpinned or `latest` artifact, contact an
external service, or upload architecture content. Never use the public Structurizr playground as an
implicit fallback.

Viewer-created `workspace.json` and manual layout are temporary review state only. Do not copy them
into the repository or present them as accepted architecture. If no viewer runtime is available,
give the actionable Docker and Java prerequisites and say that visual review has not occurred.
