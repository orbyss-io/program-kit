# Canonical knowledge discovery

The maintained owner is
`extensions/program-kit-governance/references/phase-obligations.json`.
Its existing responsibilities and source routes are extended with rule identities,
typed source locations, applicability, execution/evaluation bindings and explicit
old-to-canonical mappings. There is no additional consumer catalog to maintain.

From the repository root:

```powershell
python extensions/program-kit-governance/scripts/knowledge_discovery.py scan --repository . --format json
python extensions/program-kit-governance/scripts/knowledge_discovery.py catalog --family modularity
python extensions/program-kit-governance/scripts/knowledge_discovery.py catalog --rule native.allowed-role-references --resolve
python extensions/program-kit-governance/scripts/knowledge_discovery.py validate --repository .
python tests/knowledge_review_fixture.py --review
```

The last command prints a retained review index. Open it first: it explains the
fictional scenario, where to look, what each output means, the expected failures,
before/after differences and the precise limits of the demonstration. Review mode
keeps the consumer and snapshots until the human finishes reviewing. Another run
creates a new directory. Ordinary automated validation owns and cleans its own
temporary fixture. Failed reviews remain available for diagnosis.

`scan` explicitly enumerates the actual Git tree across references, accepted
decisions, prompts, scripts, schemas/build settings, templates/examples, independent
tests, captures and retained research. Ordered discovery scopes classify each found
source's purpose. A declaration outside active support stays explicitly available
reference, mechanism, example/counterexample, policy carrier or history. Logical
publisher documents are enumerated from exact original manifests even when stored
in packs. Scanning does not execute source, contact a publisher, select a new profile,
or establish that a historical consumer consulted anything.
Source inspection identifies named Python tables and policy-like literal locations,
schema pointers, build declarations, EditorConfig keys and C# contract/policy leads.
It emits locations rather than literal values. Keywords also occur in diagnostics
and examples, so candidates require owner review before adoption. Parse errors and
inspection bounds remain explicit; scanning is not a universal prose interpreter.

`catalog` groups attributable rule records by purpose. `--resolve` reads the selected
canonical declarations; `--format json` exposes their metadata and fingerprints.
Use `--requirement <existing-id>` or `--rule <rule-id>` for focused output. Repository
ADRs and exact Git history are maintainer sources. Installed-only resolution
(`--installed`) reports their unavailability explicitly. Publisher resolution needs
an explicit `--profile <exact-id>` or the consumer's selected effective context; it
uses the existing qualified-profile and packed-document reader. It substitutes no
new default for a missing consumer capture.

The source selectors are deliberately bounded:

| Source | Address | What the result establishes |
| --- | --- | --- |
| Prose | Stable marked rule or unique heading | Canonical authored text, with the original responsibility grouping retained |
| Python | Module symbol/table, including referenced module assignments | Declaration source without importing/executing the submitted file |
| JSON/schema | JSON Pointer and local reference closure | Selected declaration and local dependencies; external/dynamic references remain visible |
| MSBuild/XML | Element/identifying attributes plus ancestor conditions/imports | Source declaration context, not the evaluated effective project |
| EditorConfig | Section/key and ordered declaration context | Source setting, not effective nested/project/generated-code classification |
| Publisher | Exact profile and logical document | Original capture identity/digest, not consumer registration or execution |

Rule fingerprints include selected declaration content and the effective routing/
compatibility metadata. Full source hashes remain separate attribution. A selected
rule change makes its prior derived view stale; unrelated text in the same source
does not change another rule's fingerprint. These are local comparison inputs, not
an acceptance receipt or a complete F7 evidence lifecycle.

The native architecture tables own their exact executable constraints. Prose owns
additional semantic conditions; validators establish only what they actually check.
For example, a structurally allowed Core edge does not prove that the accepted
Context Map/ADR and semantic conditions permit it. Independent negative tests remain
authored against invalid behavior, not generated from catalog values.

Active phase briefs now resolve rule bindings instead of rendering the registry's
retained policy summaries. Existing requirement IDs, phase commands, `--only` and
bootstrap marker resolution remain compatible. The default brief links complete
canonical sections and uses labeled excerpts; `--only` resolves the full applicable
text. Redundant summary/example fields are retired from the active registry. Historical inspection reads original retained feature records; fixture-only historical projections use their exact original catalog.

The registry's migration rows distinguish replaced active rendering from remaining
policy carriers in version adapters, source-style guidance, commands and presets.
The existing migration mapping records replacement consumers and scoped installed proof. Do not
interpret registration, a source match or a passing fixture as removal of every
policy duplicate, semantic qualification of every package, or completion of F2–F8.
