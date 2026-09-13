# Readiness continuation input repair

Consumer: `program-kit-intake-3yd5a74k`. Original run: `ef606c1a`.
Failed continuation: `ef606c1a-r-85e58695`, at `recovery-require-ready`.
The 18,080-token assessment reported only `READINESS-CURRENT-EVIDENCE`.
Its recovery approval and governance evaluation succeeded; the assessment could
not read its supplied handoff. This was not evidence of another architecture defect.

## Verified causes

`bootstrap_recovery.prepare` used `tempfile.mkdtemp` and renamed the resulting
directory into the workspace. Its protected Windows DACL granted only the owner,
SYSTEM and administrators access. The owner process could read it; the sandbox
could not. Python documents private access for
[`mkdtemp`](https://docs.python.org/3.13/library/tempfile.html#tempfile.mkdtemp)
and owner/administrator access for Windows
[`mkdir` mode 0o700](https://docs.python.org/3.13/library/os.html#os.mkdir).
The observed ACL and sandbox denial match this mechanism.

The continuation also supplied correction prose rather than the compact readiness
context expected by the installed skill. It omitted the structured evidence index
and terminal command. Restoring access alone would not satisfy that input contract.
Earlier simulated readiness skipped reading the actual input, so it missed both
problems. Those tests established workflow mechanics, not live readiness acceptance.

## Repairs and adjacent failure checks

- Future published recovery directories use exclusive, uniquely named workspace
  directories with inherited permissions. Atomic publication and original hashes
  remain. The existing consumer directory had its workspace inheritance restored
  with `icacls /inheritance:e` on that exact directory, not a recursive permission
  reset or global/sandbox change. All 59 file hashes stayed unchanged.
- A native preparation step now builds and validates current readiness context in
  the continuation's own run directory. Confirmed intake comes from the original
  run only after checking lineage and preserved authority. Original run files are
  not rewritten. Missing sources, changed authority and invalid lineage stop
  before paid dispatch.
- The compact readiness projection retains ADR paths and `supersedes` links;
  cataloged ADRs are available for targeted evidence queries. This prevents the
  compact reading boundary from withholding the decision that replaces obsolete
  conditions. It does not require reading every ADR in full.
- The output contract and terminal instructions share one command generator.
  Readiness requests JSON so evaluation validity, verdict and completion eligibility
  are explicit. A valid NOT READY assessment does not mean bootstrap completed.
- The known saved 0.12.0 continuation migrates only its readiness suffix to 0.12.1.
  Its failed state/workflow are archived first; original lineage and approved prefix
  remain. Unknown suffixes are rejected. The exact input-access blocker retries
  readiness after authority validation rather than redoing approved recovery work.
  Interrupted readiness refreshes its context before continuing.

## Evidence

Preserved artifacts are under `artifacts/readiness-context-repair/`:

- `preflight.json`: all four compatibility proofs remain valid; original approval,
  report, result and both run records remain unchanged. Final generated context is
  70,894 bytes with SHA-256
  `bdf8ce14545ef9413b719eeaedb172ea728f234fbaa50a94b8331c8c7d93ac02`.
- `recovery-hashes-before.json`, `recovery-acl-before.txt`,
  `recovery-acl-after.txt`: exact directory repair and unchanged content.
- `sandbox-readability.json`: the sandbox read all 29 declared input/evidence paths
  and executed the supplied terminal contract with Python 3.12. The owner-side
  preflight used the actual Spec Kit Python 3.13 interpreter.
- `consumer-simulation-final.json`: an isolated copy of the actual consumer completed
  native migration, context generation, evaluation, eligibility and completion binding.
  All ten successful prefix results, approval and four proofs survived. Exactly one
  explicitly simulated readiness producer ran; no coding agent was launched.

The native regression now consumes and checks the generated context/evidence contract,
tests old-suffix migration, rejects unapproved drift and invalid lineage, and retains
semantic NOT READY, review, interruption and completion checks. The lifecycle regression
checks the published Windows directory's actual DACL protection flag. The earlier
test-only PowerShell-host failure was corrected to use the available host. The copied
consumer simulation excludes disposable build/package caches and validates every
bound proof input and result that acceptance actually consumes.

The bounded Development suite passed:
`artifacts/readiness-context-development-final.log`.
No paid agent run or live semantic readiness assessment is claimed by these checks.
The real consumer remains failed until the user resumes and the live assessment runs.
That assessment may still identify substantive issues; deterministic recovery tests
cannot establish its future verdict or the first feature's implementation quality.

## User continuation

From the user's existing CMD terminal:

```cmd
cd /d C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-3yd5a74k
python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id ef606c1a
```

Use plain resume: the prepared-recovery flag applies only when first creating a
continuation. This follows the existing child, preserves the approved prefix and
starts a paid readiness reassessment after deterministic context preparation. No
new intake, compatibility execution or repeated architecture approval is needed for
this technical retry. The user should return its final status before starting a feature.
