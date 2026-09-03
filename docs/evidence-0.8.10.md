# Program Kit 0.8.10 correction evidence

PriceCalculator's first 0.8.9 upgrade attempt exposed two independent defects.

Spec Kit 1.0.4 remote workflow and bundle updates launched from Codex Desktop on Windows terminated
with `OPENSSL_Uplink(...): no OPENSSL_Applink`. The Codex runtime PATH contained multiple native
OpenSSL distributions before the uv-installed Spec Kit launcher. Program Kit does not own that
transport process and does not weaken TLS, rewrite PATH, or copy DLLs to mask it. The upstream
report is [github/spec-kit#4433](https://github.com/github/spec-kit/issues/4433).

The local `bundle install <release>/bundle.yml --offline` fallback then reported success and advanced
the bundle record while installed workflow, extension, and preset content remained on 0.8.8. The old
Program Kit validator compared the bundle, workflow, and extension versions, but omitted the preset
registry and managed baseline. It could stop later governance work, yet the bundle command itself
still looked successful and old `dotnet_sync` code could report false convergence.
The upstream atomicity report is
[github/spec-kit#4434](https://github.com/github/spec-kit/issues/4434).

After the components were repaired, PriceCalculator exposed a third defect in Program Kit itself:
constitution validation required the immutable bootstrap profile version to equal the installed
version. That made a correctly approved later upgrade impossible to represent without rewriting a
hash-bound historical decision. The standalone constitution command also began the amendment but
did not validate the resulting draft or regenerate its review packet before ratification.

The correction supplies a release-owned updater rather than trusting bundle orchestration. A single
exclusive lock covers a strictly sequential bundle/workflow/governance-extension/.NET-extension/
preset sequence. The bundle operation resolves composition metadata, every primitive is then
installed explicitly, the previous preset is deliberately replaced because Spec Kit has no preset
force option, and an existing .NET baseline is synchronized and checked. The final governance gate
compares all manifests, registries, bundle contribution records, and managed-baseline version before
printing success.

When a bootstrap decision register exists, the updater also records Accepted version authority only
after component coherence succeeds. The record is bound to the immutable decision-register hash and
names the original baseline, prior installed release, and current installed release. Governance
accepts the version difference only through that exact evidence. A mandatory post-constitution hook
runs draft validation and review-packet generation in order before the human gate.

Regression coverage uses the installed Spec Kit CLI against a disposable consumer with deliberately
old manifests, registries, bundle records, and managed state. It proves ordered mutation, managed
sync convergence, final version coherence, immutable bootstrap history, Accepted upgrade evidence,
constitution amendment validation/review/ratification after an upgrade, rejection of unrecorded
version drift, and rejection of a pre-existing upgrade lock.
