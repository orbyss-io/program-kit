# Native BFF ticket renewal after completed logout

Date: 2026-10-28. **Confirmed in published Foundation 0.3.8; native correction
published in Foundation 0.3.9 and qualified as a new Program Kit profile.**

## Finding

Foundation 0.3.8, source `2b5f6737e558977fd17cd83fe1e03d0b96aa0df4`, can restore a
ticket removed by completed native local logout. Both automatic sliding renewal
and explicit renewal of an existing authenticated ticket reproduce the defect.

The experiment uses the published native BFF feature, actual CShells HTTP
pipelines, `CookieAuthenticationHandler`, `DistributedTicketStore` and
`MemoryDistributedCache` on ASP.NET Core **10.0.14** inside the selected image:

`ghcr.io/orbyss-io/foundation-host@sha256:bf27d204ee972b6aadf3b156b493773e7c6e6ae9a3bf010a30b46c6d88b5e93a`

A authenticates and waits at a barrier. B completes the actual antiforgery-protected
`/bff/logout`, including local deletion and native provider-unavailable fallback.
The ticket is absent and replay is denied. A resumes, writes the same key and
emits a late session cookie. Both the old cookie and the late cookie then
authenticate. This affects session and persistent cookies.

| Published 0.3.8 experiment | Result |
| --- | --- |
| Completed logout before sliding renewal, both persistence settings | Deleted ticket restored; old and late cookies accepted |
| Completed logout before explicit renewal, both persistence settings | Deleted ticket restored; old and late cookies accepted |
| Ordinary idle expiry | Access denied |
| Sliding or explicit renewal resumes after idle expiry | Expired key restored and accepted |
| Sliding or explicit renewal resumes after original absolute expiry | Late cookie emitted, but rejected; ticket absent |
| Fresh intentional login after logout | Distinct key created; removed key stays absent |
| Foreign-shell HTTP replay and shared-cache read/remove/renew | Isolation preserved |

Absolute-expiry controls keep the ticket's idle deadline beyond the absolute cap,
preventing earlier idle expiry from masking the test. An authenticated in-flight
request can still finish after logout. The defect is that later requests
authenticate because renewal recreated its session.

## Native correction

The [original Foundation store](https://github.com/orbyss-io/dotnet-foundation/blob/2b5f6737e558977fd17cd83fe1e03d0b96aa0df4/src/Orbyss.Foundation.Authentication.BffCookie/DistributedTicketStore.cs)
creates keys through `RenewAsync`, which unconditionally calls `SetAsync`.
`RemoveAsync` independently deletes the key. There is no conditional-update fence.
Shell ownership and the original absolute cap protect different invariants.

The [ASP.NET Core 10.0.14 handler](https://github.com/dotnet/aspnetcore/blob/v10.0.14/src/Security/Authentication/Cookies/src/CookieAuthenticationHandler.cs)
retains a successfully read session key per request. Automatic response renewal
and explicit sign-in can renew that key after another request signs out.
Sign-out state is request-local. The
[10.0.14 memory cache](https://github.com/dotnet/runtime/blob/v10.0.14/src/libraries/Microsoft.Extensions.Caching.Memory/src/MemoryDistributedCache.cs)
upserts on set; prior removal does not fence subsequent writes. Runtime experiments
independently establish the resulting behavior.

Implemented Foundation commit:
[`f2331c8c40761521d0c44528323fd4b7e535484d`](https://github.com/orbyss-io/dotnet-foundation/commit/f2331c8c40761521d0c44528323fd4b7e535484d).

- `StoreAsync` alone creates a fresh key and original absolute deadline.
- `RenewAsync` requires a live existing entry, preserves its server-owned cap and
  refuses missing, removed or expired entries. Caller-supplied cap changes cannot
  extend the current server session.
- Default memory-cache creation/read/renew/removal share synchronization across
  stores using that cache. Synchronization is bounded per cache instance with
  weak cache ownership; there is no growing per-session lock map.
- Custom distributed caches must implement native
  `IBffSessionTicketCache.TryRenewAsync`: backend-atomic live-byte comparison and
  replacement ordered with expiration, removal and independent clients. Unsupported
  caches fail explicitly. An unlocked read/set or local lock does not establish
  cross-process safety.
- Refused renewal can still produce a late opaque cookie through the handler.
  The server rejects that cookie; no session is recreated.

Package documentation explains the cache-extension compatibility requirement.
No remote backend implementation is supplied or qualified here. Conditional-provider
tests use an explicit in-memory contract fixture and do not qualify arbitrary
distributed backends.

## Regression and retained behavior

Foundation's maintained BFF probe includes `TicketRenewalProbe` and
`TicketCacheContractProbe`. Its existing entrypoint runs them; `--ticket-renewal`
selects the focused case. Existing CI/release browser scenarios run the new
`ticket-renewal-race.cjs`, retaining Firefox for CI.

The regressions cover:

- Completed logout before sliding/explicit renewal for session/persistent cookies:
  absent server key and denied old/late cookies after A completes.
- Ordinary idle expiry, late renewal after idle expiry and original absolute cap.
- Valid sliding/explicit renewal extending idle access while preserving principal,
  tokens, authentication properties, persistence and the server-owned original cap.
- Direct renewal of missing/removed keys and attempted cap replacement.
- Two native stores sharing the actual memory cache, with a barrier inside the
  protected cache read: removal/read cannot bypass synchronization and final
  removal wins.
- An independent store removing or changing a backend value before atomic
  comparison: stale renewal cannot recreate or overwrite it.
- Fresh intentional login, foreign-shell HTTP replay and shared-cache isolation.
- Actual browsers processing logout's deletion before A's late `Set-Cookie`:
  the late cookie is observed but both it and the old cookie are denied.

Local validation of the unpublished working-tree candidate completed in **50.552
seconds**, with separate drained streams and source-content bindings retained
locally. Locked restore, Release build, maintained BFF validator, provider-neutral
boundary, source metadata, package build, diff checks, exact Linux-image execution,
Chromium/WebKit late-cookie races and the existing browser login/recovery/logout
scenario passed. The packed BFF assembly matched the tested source build byte for
byte. The unrelated full Foundation inventory was not run locally. Firefox is
not runnable on this Windows host; its affected CI scenario remains required.

The new regression was compiled against the original store in a disposable source
copy. Compilation succeeded; execution failed specifically at
`Late renewal restored a logged-out session`. This is a behavioral negative,
not a compiler/setup failure. Initial metadata-binding and test-import build
failures were preserved and corrected before final validation.

These local checks establish candidate behavior, not consumer confirmation.
Subsequent [exact-source Windows/Linux CI](https://github.com/orbyss-io/dotnet-foundation/actions/runs/40719451125)
passed, including the required Firefox scenario. [Foundation 0.3.9](https://github.com/orbyss-io/dotnet-foundation/releases/tag/v0.3.9)
is published from `f663ab74f0b83be84ff9bdd8f16d92eae49d5a09`; its
[Release workflow](https://github.com/orbyss-io/dotnet-foundation/actions/runs/40722524484)
succeeded on attempt 2. Attempt 1 uploaded all 30 runtime packages but timed out
waiting for two NuGet packages to propagate. The original failure is retained;
after all packages became public, their source commits and compiled payloads
matched successful exact-source CI. Recovery used the same source/tag, with no
version increment, tag movement or differing-source replacement. Host publication
and exact release knowledge then completed. Version 0.3.8's immutable published
artifacts have not been replaced.

Public release knowledge SHA-256:
`7b1075a20cee21b15f9299cebe3733b5d275f0bef6ec4b5cce7406d50e7a965f`.
Published Host:
`ghcr.io/orbyss-io/foundation-host@sha256:ad52ade8e0750fb61b2fde5eaae4b218ba5e79db39970efe421e7471c4e19f98`.

## Published-version reproducer

The [locked diagnostic](../../tests/fixtures/bff-ticket-renewal-race/README.md)
preserves the affected published release for independent reproduction:

```powershell
python tests/fixtures/bff-ticket-renewal-race/run.py --output artifacts/auth-race/<new-run>
```

It verifies archives against retained profile qualification, builds and starts
the diagnostic inside the exact cached Host image with external networking
disabled. It starts real shell HTTP pipelines rather than the Host application's
entrypoint. The store is unmodified; a forwarding observer records new keys.
Controlled clocks and barriers provide deterministic expiry/order. Identities
and provider metadata are fictional; cookie values are not printed.

Eleven cases reproduced the original issue in 3.449 seconds with warm caches;
21 restored archives matched qualification hashes. **Exit zero means the
vulnerability reproduced, not that authentication passed acceptance.** This
investigation-only fixture stays outside the validation inventory. Its unmapped
paths are an explicit coverage limitation, not a release safety gate. Fixed
behavior belongs to the native Foundation regressions above.

Program Kit Integrity passed. Affected selection included unrelated existing
repair-feedback edits; their sandboxed Git Bash check initially failed with access
denied and the unchanged focused check passed with external-process access.
The original Affected result and diagnostic coverage gaps remain visible;
no complete Affected acceptance is claimed. Private consumer context and full
local execution records remain outside this commit.

## Versions and adoption

Runtime-confirmed affected version: **Foundation 0.3.8** at `2b5f6737`, with the
exact image/runtime above. Source at tags `v0.2.0`–`v0.2.4` and `v0.3.0`–`v0.3.8`
contains the unconditional renewal write; earlier releases were not independently
executed. The current source path is absent at `v0.1.0`, which alone does not
establish that version is unaffected.

The affected Program Kit profile is
`foundation-0.3.8-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2`.
Historical qualification does not prove the renewal/revocation invariant.
Automatic native sliding is affected independently of an application activity
adapter. Disabling sliding does not repair explicit renewal; browser generation
fences do not stop server upserts or native response headers.

[Program Kit maintenance](https://github.com/orbyss-io/program-kit/actions/runs/40730144795)
qualified the public packages, actual Host and versioned publisher knowledge as:

`foundation-0.3.9-build-0.3.3-exporter-0.2.7-forms-0.2.1-localization-0.1.2-analyzer-0.3.8`.

[Maintenance PR #62](https://github.com/orbyss-io/program-kit/pull/62) adds the
profile without altering any of the 14 historical profile registrations. Build,
exporter and analyzer keep their independent versions. The captured runtime source
includes `IBffSessionTicketCache` and the corrected store. The profile's actual
Host digest matches the completed Foundation release above.

Consumer toolkit refresh supplies that qualified default and its native guidance;
it preserves existing consumer locks and authored specifications. It does not
materialize application composition, migrate dependencies, or demonstrate a consumer
runtime. A consumer planning against 0.3.8 must explicitly reconcile the corrected
profile and native cache seam before implementation. Preserve historical qualification
and locks. Application activity policy, remember-intent transfer through OIDC and
actual consumer acceptance remain their own checks.
