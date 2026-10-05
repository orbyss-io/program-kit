# Application engineering

This directory is application engineering source/configuration. Keep it with the application.
Its commands do not import Spec Kit extensions, governance validators, decisions or AI workers.
The repository's native projects, dependency locks, analyzer configuration, contract baselines,
architecture policy and deployment inputs are the engineering authorities.

From the repository root (PowerShell and Python are normal engineering prerequisites):

```powershell
./eng/Restore.ps1 -LockedMode
./eng/Invoke-RepositoryVerification.ps1
python eng/openapi_pipeline.py --repository .
./eng/Build.ps1 -LockedMode
```

Restore uses the pinned SDK and repository NuGet routes. Verification runs the consumer's
eng/verify.ps1 when supplied, then compiled architecture checks; otherwise it runs the standard
build/tests. Build also stages the application release bundle for the selected published host.
Contract generation runs registered contracts and compares their baselines. A deliberately accepted
contract change can update its baseline explicitly; never bypass an unexpected compatibility failure.

Declare actual project roles and scoped dependency exceptions once in eng/architecture.json.
Native MSBuild/compiled assemblies supply real dependencies. An exception needs a rationale and an
existing verification test. Record the substantive approval in normal review or an ADR. No document
hash or ratification receipt is needed to compile. Domain semantics and security behavior still need
application tests and code review; green analyzers alone cannot establish them.

Generated files, caches and logs belong under ignored artifacts/. Keep deployment source, native
locks, analyzer policy, tests and baselines in Git. A human can edit projects and run these commands
with no AI, .specify/, .program-kit/, specifications or governance documents installed.
