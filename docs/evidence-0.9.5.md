# Program Kit 0.9.5 correction evidence

The v0.9.4 tag exposed two environment-dependent release failures after passing the deterministic
Windows release suite. GitHub Actions supplies `GITHUB_SHA`, causing the Git-safety regression to
short-circuit before its mocked subprocess assertion. GitHub's runner also contained SDK `10.0.204`;
the repository's `latestPatch` policy selected it even though Program Kit's toolchain contract
correctly required exact SDK `10.0.202`.

The regression now temporarily removes and restores inherited `GITHUB_SHA` around the subprocess
checks, preserving production behavior while testing the intended path on every runner. Both root
and generated-consumer `global.json` files now use `rollForward: disable`, aligning SDK resolution
with the exact managed toolchain prerequisite.

All shell-composition, packaged authentication, OpenAPI, oasdiff, NuGet isolation, runtime-closure,
Keycloak, authorization-ownership, upgrade, and publication changes from 0.9.4 are otherwise retained
unchanged in 0.9.5.
