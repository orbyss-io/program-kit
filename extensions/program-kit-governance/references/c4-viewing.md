# Viewing the Program Kit C4 projection

Program Kit uses `docs/architecture/architecture-map.json` as the semantic source of truth and
generates `docs/architecture/workspace.dsl` only as a review projection. Viewing must not import DSL
edits or change either canonical file.

The viewer has two read-only modes. Draft intake review is allowed before explicit confirmation only
when the intake is valid JSON, all three registered artifact hashes and byte counts match exactly,
the DSL parses, and it is byte-for-byte equivalent (apart from newline normalization) to a fresh
export of canonical `architecture-map.json`. Confirmed baseline review retains the same projection
freshness and registered-pair drift checks. Neither mode changes intake status, creates approval or
acceptance evidence, or accepts proposed architecture; the outer bootstrap workflow still requires
a confirmed intake.

Draft viewing is therefore part of informed intake review, not bootstrap approval. Review the
System Context, domain/subdomain landscape, strategic Context Map, context/module decompositions,
and each named journey view together with the text summary of founding decision candidates and
alternatives. The architecture phase later creates real Proposed ADRs, and the existing
post-architecture approval pause governs their acceptance.

## Runtime policy

Required prerequisites are Python for the launcher, a local browser, and either Docker with its
daemon running and the pinned image cached, or Java 21+ with the pinned WAR already local. The
viewer does not need Node, npm, Playwright, a coding worker, or a paid acceptance run. Report a
missing prerequisite immediately rather than searching indefinitely or silently installing it.

The managed viewer profile is `c4-viewer-tool.json`. Prefer its exact Docker image when Docker is
running and that image is already present. Otherwise use its exact-version WAR only when Java meets
the profile minimum and the WAR is already available through `--war`,
`PROGRAM_KIT_STRUCTURIZR_WAR`, or the displayed user-cache path.

Do not run `docker pull`, download the WAR, install Docker or Java, upload the workspace, or contact
the Structurizr playground without explicit user authorization immediately before that action.
Docker `run` can pull implicitly, so never run it until image inspection proves the exact pin is
local. Structurizr Lite is obsolete and is not a fallback.

The launcher stages `workspace.dsl` and locally referenced documentation/ADR inputs under the OS
temporary directory. Structurizr may create `workspace.json` there for manual layout; that file is
disposable and never supersedes the canonical map or generated DSL. The server binds to
`127.0.0.1`, starts at port 8081, and selects the next safe port when occupied.

The generated projection applies Program Kit's review theme: people are teal, software systems are
blue, bounded contexts are violet, and proposed items/relationships use orange dashed cues. These
styles are generated review metadata, not accepted architecture semantics. The launcher links
straight to the first diagram. Use the left thumbnail rail to switch views and the key control in
the diagram toolbar to decode the styling. A magnifier on an element opens a linked detail view;
when it is absent, the canonical architecture map defines no deeper C4 view. The `+` and `-`
controls zoom the canvas rather than navigating the model hierarchy.

## Commands and recovery

Run inspection first:

```text
python .specify/extensions/program-kit-governance/scripts/c4_view.py inspect --project-root . --json
```

Start a detached local viewer and open the browser:

```text
python .specify/extensions/program-kit-governance/scripts/c4_view.py start --project-root . --open --detach --timeout 120
```

Allow at most three minutes of active agent work for inspection, startup, and presentation together.
Inspection has a 30-second command budget; startup defaults to a 120-second budget shared by its
validation, runtime probes, child commands, and readiness checks. `--timeout` can shorten startup
but cannot extend it beyond 120 seconds. Failure diagnostics and cleanup have a separate bounded
30-second budget. The browser opener has a five-second timeout. Never retry automatically after a
failed inspection, start, workspace load, or browser attempt; end with one blocker and next step.
An agent must always use detached mode. Foreground mode is only for a human-owned terminal.

The launcher checks the actual diagrams page and the local workspace API for the selected view,
including for reused sessions. It does not claim a completed browser render or human visual review.
The successful start output includes the exact diagram URL, navigation hint, and stop command.
If browser opening fails or is unavailable, immediately give the URL for manual opening and stop.
A foreground start (omit `--detach`) prints the URL before waiting and cleans up on Ctrl+C.
Stop either mode explicitly with:

```text
python .specify/extensions/program-kit-governance/scripts/c4_view.py stop --project-root .
```

On startup failure, the launcher captures the last 200 Docker log lines or preserves the Java
streams, stops its newly started runtime, and saves logs plus `failure.json` under the displayed
temporary `program-kit-c4-view/failures/` path. Failed containers are retained until this capture;
successful stop still removes the container and temporary session. Evidence is local and can
contain architecture details: inspect only a bounded excerpt relevant to the blocker, never upload
it or print full logs. If cleanup fails, session state remains available for the exact stop command.
Reused sessions that fail readiness are left intact; report the blocker and stop command, without
killing an unverified process or repeatedly restarting it.

Permission denied for Docker or localhost can reflect the agent's sandbox rather than absent tools.
Use the integration's supported permission mechanism once when authorized, or provide the exact
detached start command for a normal local terminal and stop. Do not change the consumer's model,
disable the sandbox, or claim a successful visual review to work around the restriction.

If inspection reports a missing image or WAR, present the exact pin and local cache location, ask
whether the user authorizes that specific retrieval, and stop. If neither Docker nor Java 21 is
available, explain both requirements without claiming a visual review. Static SVG/PNG review
packets remain an optional future mode because the upstream exporter needs the separate Playwright
binary variant; they are not an intake-validation dependency.
