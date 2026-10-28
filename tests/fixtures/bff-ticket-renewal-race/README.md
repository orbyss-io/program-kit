# Foundation 0.3.8 ticket renewal diagnostic

This is a deterministic reproduction of the native BFF ticket renewal/logout race.
Exit zero means the **vulnerability reproduced**, not that authentication passed
acceptance. It deliberately pins the affected published release; it must not be
used as a release safety check or silently updated to a corrected version.

From the Program Kit root, with the existing .NET SDK, Docker daemon and exact
Host image available:

```powershell
python tests/fixtures/bff-ticket-renewal-race/run.py --output artifacts/auth-race/<new-run>
```

The runner performs locked NuGet restore, compares downloaded archives against
the retained profile qualification, builds and executes inside
`ghcr.io/orbyss-io/foundation-host@sha256:bf27d204ee972b6aadf3b156b493773e7c6e6ae9a3bf010a30b46c6d88b5e93a`.
It records both streams, commands, hashes, durations and observed runtime/source
identity. It installs no toolchain. It requires a new output directory per run.

The executable starts real CShells HTTP pipelines and the published native BFF
feature. A forwarding ticket-store observer records new-session keys; it delegates
all reads, renewals and removals unchanged to the native store. The selected cache
is the actual `MemoryDistributedCache`. Only its clock and the cookie handler's
clock are controlled for deterministic expiry. Native store creation still uses
its actual `DateTimeOffset.UtcNow`. The fixture never changes protected cap metadata.

`TaskCompletionSource` barriers pause request A after native authentication and
before response completion or explicit `SignInAsync`. Request B completes actual
antiforgery-protected `/bff/logout`, including local deletion and native provider
fallback, before A resumes. Replay requests explicitly send the old or late cookie.
Cookie/header values never enter retained output. Provider metadata is fictional
and has no logout endpoint; Docker execution disables external networking.

Eleven cases cover sliding/explicit renewal with persistent/session cookies, idle
expiry and delayed renewal, delayed renewal past original absolute expiry, fresh
login and foreign-shell isolation including direct shared-cache operations.

This is an on-demand investigation fixture outside the validation inventory.
Its unmapped paths are disclosed coverage gaps, not automatic acceptance. The
Foundation correction should gain native regression tests in Foundation's own BFF
probe, independent of Program Kit. See the associated investigation report under
`docs/reviews/` for the proposed correction, evidence and qualification boundaries.
