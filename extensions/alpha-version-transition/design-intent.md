# Program Kit alpha version transition intent

## Human outcome

Program Kit is still pre-stable. Its next coordinated package release is
`0.1.0-alpha.2`, and every first-party deliverable packaged from this repository
uses that exact release identity. The capability bundle must not maintain an
independent content release number such as `3.0.0`.

Program Kit-owned schemas, contracts, policies, capability definitions, static
dispositions, plans, designs, and comparable governed artifacts have identities
and revision histories that are independent of the product release. During
alpha, each changed identity advances by replacing its current revision number
with `0.1.0-alpha.N`, where `N` is the one-based revision ordinal for that
identity. In particular:

- Architecture Design revision 2 becomes `0.1.0-alpha.2`;
- Implementation Plan revision 3 becomes `0.1.0-alpha.3`; and
- StaticConformanceDisposition revision 1 becomes `0.1.0-alpha.1`.

The SemVer spelling uses a hyphen: `0.1.0-alpha.N`.

Package identity and contract identity are different version intents. Matching
numbers between independent identities never imply compatibility.

## Alpha policy

The alpha policy is deliberately replaceable:

- a new Program Kit-owned governed identity starts at `0.1.0-alpha.1`;
- changing canonical bytes under the same identity requires the next alpha
  ordinal;
- the same identity, version, and digest denote the same immutable revision;
- every contract change records compatibility and migration disposition;
- no patch/minor/major compatibility classification is enforced before the
  first stable release; and
- Release Kit will later define the stable progression policy and the transition
  to `1.0.0`.

Program Kit validates an explicit version decision. It does not infer product
release authority, choose a new version autonomously, or silently upgrade a
consumer.

## Version intents

The transition distinguishes:

1. **Product release identity** — the coordinated version of all first-party
   NuGet packages, the CLI, the capability bundle content, and generated
   first-party package references.
2. **Owned artifact revision** — an independent revision of a stable Program
   Kit-owned schema, contract, policy, capability, plan, design, or comparable
   governed identity.
3. **External selection** — an exact upstream SDK, target framework, tool,
   analyzer, or third-party package version; Program Kit records but never
   renumbers it.
4. **Historical evidence revision** — immutable approval, closure, or receipt
   evidence; Program Kit does not rewrite it to make current numbering look
   uniform.
5. **Fixture revision** — an explicitly synthetic test identity whose values do
   not claim product or public-contract release status.

A bundle-manifest format revision is an owned contract revision separate from
the product release carried by the bundle.

## Transition and migration

The current stable-looking and high-major contract revisions remain immutable
legacy revisions. The transition adds alpha replacement revisions, registers
explicit old-to-new migration definitions, and updates active selectors only
after deterministic compatibility and migration verification.

The transition must cover the complete active Program Kit-owned artifact
inventory. External selections, immutable historical evidence, and intentional
fixtures remain unchanged and explicitly classified.

The design, planning, and static-conformance contracts move first so the
remaining Program Kit health work can be designed under the corrected alpha
contracts. Canonical capability procedures and thin provider wrappers must be
updated and re-bundled without activating the source capabilities in the
Program Kit authoring workspace.

## Follow-on health design

After the transition is implemented and verified, a separate exact review set
will cover:

- deterministic capability refresh and re-initialization for an already
  initialized consumer;
- replacement of the unclear bootstrap contributor experience with a
  `.contributors` maintainer-workspace setup rooted in the parent of the
  Program Kit checkout;
- Console CLI generation and refresh reachability with exact .NET binding,
  reference-assembly, and compilation-reference inputs;
- public, opt-in reusable C# contract analyzers without publishing private PKCS
  repository policy; and
- a bounded JTest migration prompt and consumer-side verification sequence.

No JTest repository mutation, contributor workspace mutation, package
publication, or runtime implementation is authorized by this review set.

## Human decisions represented

The human explicitly selected the next product version
`0.1.0-alpha.2`, the alpha ordinal approach for Program Kit-owned contracts,
the two-stage transition, and reuse of
`pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`.

The human approval statement for these recommendations was:

> i approve all recommendations and fixes

That statement approves the design direction and static-conformance selection.
It is not approval of canonical design or implementation-plan bytes that had
not yet been produced.
