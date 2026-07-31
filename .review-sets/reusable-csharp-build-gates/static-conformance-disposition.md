# Candidate static-conformance disposition

- Artifact identity:
  `pkid:static-conformance-disposition:program-kit:reusable-csharp-build-gates@1.0.0`
- Design:
  `pkid:design:program-kit:reusable-csharp-build-gates@1.0.0`
- Candidate disposition: `reuse-existing`
- Decision state: candidate for the same exact human design/plan decision
- Gate selections: one
- Temporary activation exceptions: none
- Implementation authority: none

## Selected gate

The implementation of this Program Kit extension continues to use the
repository-private:

`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`

through `tools/Orbyss.ProgramKit.CSharpGate`. This selection applies only to
Program Kit-owned handwritten and generated C# in the Program Kit repository.
It does not select, package, publish, migrate, or attach the private analyzer
for any consumer.

Exact reviewed source anchors:

| Artifact | SHA-256 |
| --- | --- |
| `governance/csharp-source-quality-gate.md` | `e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1` |
| `Directory.Build.props` | `e44cca464cdb20276381c1a0866b1e2270c7db58f79c59ca8ce2888fcb08c1c7` |
| `Directory.Build.targets` | `c9340d694dbee6b1491a9293c375c211633b9e9b22347a180ed53ed5740bbb71` |
| `tools/Orbyss.ProgramKit.CSharpGate/Orbyss.ProgramKit.CSharpGate.csproj` | `1df4ea9a6845002be3974871d564ecdd625d5387112343d940bf27c421f7204a` |
| `tools/Orbyss.ProgramKit.CSharpGate/Analysis/ProgramKitCSharpGateAnalyzer.cs` | `c8a2673c31185d0c62215b3f278b981cd6c20f1eb736853f243109d0347f8768` |
| `build/Invoke-CSharpGateTestPlan.ps1` | `80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d` |

The implementation preflight must resolve these anchors to a compatible
current private-gate selection. The approved implementation plan may update
them through ordinary Program Kit source changes, but every work unit remains
subject to the current private gate and must record the resulting exact
revision in its evidence.

## Activation

The existing repository build spine remains authoritative:

- projects: every Program Kit C# project covered by the current physical-source
  inventory and explicit project rules;
- inputs: Program Kit-owned handwritten C#, Program Kit-owned generated C#,
  additional files, analyzer configuration, suppression ledger, compiler
  references, and controlled build definitions;
- commands: restore/build participation plus gated `build`, `test`, `pack`,
  `publish`, and generated-project verification as defined by policy;
- implementation boundaries: preflight, every gate-establishment work unit,
  every other work unit, generated output, and final closure; and
- profiles: focused verification during each unit and the existing exhaustive
  private-gate test plan at closure.

The exact current MSBuild properties and targets remain the executable
activation source until a separately approved migration replaces them.

## Layer allocation

| Invariant | Enforcement layer |
| --- | --- |
| Program Kit private source layout and behavioral rules | Existing private `PKCS...` analyzer |
| Private warning/suppression policy | Existing analyzer, ledger, and build targets |
| Analyzer attachment, input inventory, compiler participation, and tamper checks | Existing Program Kit MSBuild build spine |
| New public gate contracts and schemas | Schema/model validation and conformance tests added by the approved plan |
| Public Program Kit contract diagnostic semantics | New narrow `PKCC...` analyzer components only after their owning public contract and fixtures exist |
| Consumer-specific diagnostic semantics | Fictional proof consumer during this extension; real consumer-owned analyzers in separately approved consumer plans |
| Runtime, semantic, migration, compatibility, and human-quality claims | Architecture tests, executable tests, migration fixtures, evidence review, and human review |

## Residual risks

- The current private gate is a monolith combining repository policy and
  reusable-mechanics research.
- Its MSBuild trust boundary does not claim protection from a malicious
  repository-owned build definition that forges and later sanitizes every
  in-process receipt.
- The private analyzer does not by itself prove the new public schemas,
  operations, package closure, capability procedures, or consumer composition.
- Candidate public rules extracted from current `PKCS` research may change
  ownership or meaning unless the implementation first establishes an exact
  public contract and new diagnostic identity.

These risks are accepted only if the human approves the exact final review set.
They do not justify disabling the current private gate during implementation.

## Non-static claims

Passing the selected private gate does not prove correct public-contract
ownership, consumer semantics, package compatibility, runtime behavior,
security, privacy, deterministic operations, successful migrations, capability
authority, or human architectural quality. The implementation plan assigns
those claims to separate fixtures and review evidence.

## Decision requested

Approval of the exact review-set digests accepts this `reuse-existing`
candidate for implementation of the Program Kit extension itself. Rejection or
selection of another disposition returns the review set to design; silence or
an unavailable gate does not become an empty selection.
