# Logical package-content reproducibility amendment validation

Review-set identity:
`pkid:review-set-amendment:program-kit:canonical-public-analyzer-logical-package-content@0.1.0-alpha.1`.

State: `ready-for-human-decision`.

## Source and authority checks

- repository branch:
  `codex/alpha3-canonical-analyzer-selection`;
- review-set source commit:
  `f6c824e4e1da63df326687942d82aa7a82bc82c2`;
- exact synchronized `origin/main` basis:
  `11978dc6f3cbd66cd204214318eb166cb02c3e1c`;
- exact approved base Architecture Design SHA-256:
  `59315e450e33a79a39dc1079e1587d6a6747c3343714e3dd8957fff0dddd47d5`;
- exact approved base Implementation Plan SHA-256:
  `3b49633d6bfecd0894cef27b5f5baddc71bb02ad492e7084e65b2fb48d9ccc30`;
- exact historical Static Conformance Disposition SHA-256:
  `cd8adf3db8caf4f0b719fbc4e5ad7cdf730aac94802288535559e10d93c664a0`;
- product candidate remains `0.1.0-alpha.3`; and
- repository SDK remains pinned to `10.0.302`.

The base artifacts and approval records were read and hash-verified before the
amendment was written. They are unchanged.

## Material-deviation evidence

The exact base-plan W030 verifier built the complete 30-package selected feed
from two clean absolute roots. Build and focused canonicalization/conformance
tests passed. Raw inventory comparison then failed for all 30 nupkgs.

Archive inspection established the same finite difference in each package:

- one random core-properties part filename;
- the matching relationship ID/target in `_rels/.rels`; and
- no difference in the core-properties document bytes or ordinary package
  entry bytes.

The retained repository-owned W030 prototype correctly refuses to rewrite an
SDK-produced entry path or content under the exact approved base plan. The
generated diagnostic roots were removed after inspection and are not review
artifacts.

## Design validation

Passed:

- the amendment changes only raw unsigned candidate reproducibility and its
  dependent evidence semantics;
- compiler-output reproducibility remains exact;
- package ID/version/role/dependency and logical-content reproducibility remain
  complete-set requirements;
- the logical projection validates exactly one safe internal OPC
  core-properties relationship before normalizing only its generated identity;
- candidate, logical-content, and published-package hashes remain distinct;
- the publication path selects and pushes one exact attested candidate instance
  without a rebuild;
- repository-signature verification precedes published-content comparison;
- the analyzer-first irreversible phase and safe-resumption boundary remain
  explicit;
- the Static Conformance Disposition remains exactly `extend-existing` and no
  new analyzer is introduced; and
- publication, workflow invocation, SDK installation, alpha.2 mutation, and
  unlisting remain unauthorized.

## Plan validation

Passed:

- `PKRB-W010` and `PKRB-W020` remain completed historical units;
- `PKRB-W050` remains semantically unchanged;
- the serial `PKRB-W030` through `PKRB-W080` dependency order is unchanged;
- W030 has finite logical-digest validation, two-root acceptance, negative
  fixtures, and stop conditions;
- W040 preserves all three package identities without conflation;
- W060 explicitly reuses exact artifact-ID selection and prohibits fallback
  packing;
- W070 covers both exact-instance and logical-content tampering;
- W080 remains the single full closure unit and retains the manual workflow
  handoff without invocation; and
- the base plan's allowed-edit boundaries and exact synchronized private-gate
  verification profile remain in force.

## Layout and preservation validation

Passed:

- every new review artifact is beneath `.review-sets/`;
- no root `extensions/` directory was created;
- no new artifact uses `extensions/` as a current path;
- historical base-artifact literal paths are preserved without rewriting;
- baseline evidence beneath `.evidence/program-kit-baseline/` is untouched;
- generated `/artifacts/` output is not used as review authority; and
- preserved uncommitted W030 implementation work is outside this review-set
  commit scope.

## Exact candidate artifact digests

- Architecture Design amendment:
  `sha256:fe0314875012e896e4dc597288ccdf98612e6936ea1dd6ef8c58dc2f58bed979`.
- Implementation Plan amendment:
  `sha256:81eff2377f83a8eb701015731991eed71164fee87b34bcb79c1922b1041f0664`.

The hashes were recalculated from the exact candidate bytes immediately before
review-manifest materialization. The review set remains unapproved until the
human explicitly approves both exact digests and the retained
`extend-existing` disposition.

## Deliberately unavailable implementation checks

The amended W030 verifier and downstream workflow simulations cannot pass
until implementation is authorized. They were not weakened or executed as if
the design amendment itself were implementation authority. No publication or
external mutation was attempted.

