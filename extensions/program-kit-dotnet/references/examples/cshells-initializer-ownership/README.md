# CShells 0.0.31 non-owning resource admission

## Problem and supported scope

Use this temporary pattern when the selected **CShells 0.0.31** application has a disposable
resource that must remain live for its shell generation and also needs lifecycle initialization.
The native `AddShellInitializer<T>` helper preserves the concrete registration but adds a transient
interface alias returning the same object. The activation scope can dispose a singleton before the
first product operation, then the generation provider disposes it again. Scoped/transient helper
registrations can also dispose their concrete object twice. This is an upstream ownership defect,
not a reason to replace CShells, its DI container or the selected Foundation mechanisms.

The confirmed defect is tracked in [CShells issue 216](https://github.com/valence-works/cshells/issues/216).
The earlier [registration-lifetime repair](https://github.com/valence-works/cshells/pull/131) is
already included in 0.0.31; it does not fix this remaining disposal defect. Other versions require
their own selected-version evidence. This example adds no package override or automatic migration.

## Reuse the registration and admission

`ResourceFeature.cs` and `ResourceAdmission.cs` are the reusable pattern. Replace
`SyntheticResourceOwner` with the application's existing semantic resource owner and delegate to
its actual admission method. Keep the existing ShellFeature identity and selected ordering.
`SyntheticResourceOwner.cs` is a fictional memory resource and diagnostic instrumentation for
the executable regression; it is not a filesystem provider, authorization implementation or
production state manager to copy into an application.

```csharp
services.AddSingleton<ResourceOwner>();
services.AddShellInitializer<ResourceAdmission>(LifecyclePhase.Prepare, order: 200);
```

The admission class has typed constructor injection, implements only `IShellInitializer` and
returns/awaits the owner's initialization task with the original cancellation token. It does not
implement `IDisposable` or `IAsyncDisposable` and never disposes the injected owner. DI owns that
resource through its one concrete registration; native generation teardown owns its lifetime.
The initializer's temporary scope can end without closing the owner.

This bounded extra class compensates for the affected helper. It is not a general requirement
to introduce forwarding layers or duplicate already-correct native provider ownership.

## Safety and adaptation boundaries

- Keep exactly one DI disposal owner. Do not add a second interface factory returning the same
  disposable instance, even when that interface declares no disposal methods. DI inspects the
  returned object's actual interfaces. Matching alias lifetimes still allows double disposal.
- Choose the real resource lifetime. Do not promote scoped contexts, requests, users or transactions
  to singleton. A scoped/transient admission-only resource belongs to its activation scope and
  must still be cleaned up there; it is not a resource to retain for later product operations.
- Await admission before publication. Let rejection, asynchronous failure and cancellation escape;
  never catch them and activate anyway, substitute success, add an unowned retry or suppress cleanup.
  The real owner must tolerate partial initialization and dispose resources it has acquired.
- Retain all existing authorization, configuration and ownership checks. The adapter grants no
  permission and performs no additional product operation. Keep schema deployment separate;
  native runtime schema/privilege admission remains read-only and least-privileged.
- Use native tracked scopes for work and native reload/drain for teardown. Do not manually dispose
  a DI-owned singleton in a terminator, keep the activation scope open, or disable scope disposal.
  Native forced-drain limits and the owner's existing thread-safety obligations still apply.
- Initialization/destruction, cancellation and policy decisions stay with their existing owners.
  The synthetic observation gates/counters below provide test control only, not application policy.

This is safe for the exercised ownership contract when these conditions hold. It does not establish
the security or correctness of an arbitrary resource owner, erase data, run migrations, alter a
secret store, change authentication, or bypass human review.

## Focused verification and retirement

Prove the adapted real owner remains usable after **settled activation**, rather than checking only
that its initialization ran. Exercise failure/cancellation after resource acquisition, unsuccessful
replacement, reload while an old tracked scope is open, native drain and exactly-once cleanup.
Check both synchronous and asynchronous disposal where selected, and retain legitimate
scoped/transient admission cleanup. A matching-lifetime alias is a useful negative control.

The maintained on-demand native check compiles these actual example files against exact public
CShells 0.0.31, starts no Foundation Host/database/browser, and asserts the ownership boundaries.
Repository maintainers run:

```text
python scripts/run_validation.py --check validate_cshells_initializer_ownership --reason "changed selected CShells resource admission ownership"
```

Consumers adapt the two pattern files in their existing feature and use a small native shell fixture
in their existing tests. Run only when the relevant owner/registration/lifecycle input changes;
generic coding hooks neither execute this check nor start the full application. Preserve agreed
human story reviews. Installing Program Kit does not modify existing application registrations.

Until a repaired CShells release passes normal dependency qualification and the affected owner
checks, retain this adaptation. Afterwards reconsider it through ordinary source review, keeping
any meaningful admission/resource separation. Do not remove it automatically based on a newer
version number or claim that Program Kit has repaired upstream CShells itself.
