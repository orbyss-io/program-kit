# Version intents and pre-stable alpha progression

Program Kit keeps product-release identity separate from the revisions of
contracts, schemas, policies, capabilities, and other governed artifacts.
During the pre-stable transition, every version-bearing source must be
classified explicitly. A number that looks like a version is never enough to
infer its meaning.

## Version intents

The closed inventory recognizes exactly five intents:

- `product-release` coordinates first-party packaged deliverables. Its version
  is selected through separate release authority, not by an artifact validator.
- `owned-artifact-revision` identifies a Program Kit-owned governed contract or
  artifact. During this transition its explicit proposal is checked against the
  replaceable alpha progression policy.
- `external-selection` records a version selected by an external owner. The
  transition preserves it.
- `historical-evidence-revision` occurs in immutable evidence, approval,
  receipt, or closure material. It is inactive and preserved byte-for-byte.
- `fixture-revision` is an intentional test value. It is preserved unless a
  separately approved fixture change says otherwise.

Each inventory entry binds a semantic identity and owner to an exact
repository-relative source path, current text, complete-file SHA-256 digest,
active state, optional owned revision ordinal, and transition disposition.
The inventory also names finite source roots and exact completeness evidence.
The Workbench operation compares that inventory only with the caller-supplied,
bounded observation set. It neither scans an unbounded repository nor
classifies a source.

## Replaceable alpha policy

The transitional policy validates explicit revisions in the form
`0.1.0-alpha.N`:

- a new owned identity starts at the policy's explicit initial ordinal;
- unchanged canonical bytes retain the exact identity, version, and digest;
- changed canonical bytes use the next ordinal and a different digest;
- compatibility is classified explicitly as compatible or incompatible;
- an incompatible revision requires exact migration references.

The validator accepts or rejects a caller-selected proposal. It cannot choose a
version, decide whether to release, mutate an artifact, or apply stable
patch/minor/major meaning. Product release remains a separate decision.

The policy document includes an exact policy revision and a replacement-policy
contract. Release Kit can later replace the alpha mechanics with the approved
stable version strategy without changing the distinction between product
release identity and independently revised governed artifacts.
