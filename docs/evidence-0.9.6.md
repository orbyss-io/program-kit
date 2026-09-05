# Program Kit 0.9.6 correction evidence

PriceCalculator exposed four remaining consumer-boundary defects after upgrading to 0.9.5:

1. A direct locked `dotnet restore --configfile NuGet.config` passed `RestoreConfigFile` correctly,
   but NuGet 7.3.1 separately loaded proxy settings from
   `%APPDATA%\NuGet\NuGet.Config` and failed in the Windows Codex sandbox.
2. Runnable-host source resolution supplied a Windows backslash path to command-scoped
   `safe.directory`; Git 2.44 rejected the mismatched-SID worktree. The same absolute path expressed
   with forward slashes succeeded.
3. OpenAPI created a NuGet-isolated profile before renewing exact toolchain evidence, hiding an
   fnm-managed Node/npm installation beneath the original user profile.
4. OpenAPI compared runtime-closure `programKitVersion: 0.9.5` to the application's independent
   `VERSION: 0.1.0`, producing false `PKR022` evidence rejection.

Microsoft documents that `--configfile` uses only settings from the named file, and documents the
Windows user config under `%APPDATA%`; the observed proxy-cache initialization shows that selecting
settings is not a guarantee that the process performs no ambient profile read. Program Kit therefore
provides the stronger process boundary itself. See
[dotnet restore](https://learn.microsoft.com/dotnet/core/tools/dotnet-restore) and
[NuGet configuration behavior](https://learn.microsoft.com/nuget/consume-packages/configuring-nuget-behavior).

Regression coverage denies the executing Windows identity access to a real ambient `NuGet.Config`,
proves direct restore reproduces the failure, and proves the managed wrapper succeeds. Additional
tests assert inherited isolation for consumer-owned verification, forward-slash Git trust on the
actual mismatched-SID PriceCalculator checkout, atomic preservation of satisfied toolchain evidence,
tool discovery before NuGet isolation, and OpenAPI success with application version `0.1.0` against
the independently managed Program Kit baseline.

Git's supported protected `safe.directory` mechanism remains command-scoped as described by
[git-config](https://git-scm.com/docs/git-config#Documentation/git-config.txt-safedirectory). No
global setting or wildcard trust is introduced.
