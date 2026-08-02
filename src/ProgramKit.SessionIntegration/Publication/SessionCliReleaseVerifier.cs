using System;
using System.IO;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed record SessionCliReleaseContract(
    string PackageId,
    string PackageVersion,
    string CommandName,
    GovernedIdentity RuntimeProfile)
{
    public static SessionCliReleaseContract Current(string packageVersion) => new(
        "Orbyss.ProgramKit.Cli",
        packageVersion,
        "program-kit",
        new GovernedIdentity(
            "dotnet",
            "runtime-profile",
            "net10.0",
            "10.0.0",
            Digests.Sha256(System.Text.Encoding.UTF8.GetBytes("program-kit runtime profile v1\n.NETCoreApp,Version=v10.0"))));
}

public sealed class SessionCliReleaseVerifier
{
    private readonly SessionCliReleaseContract expected;

    public SessionCliReleaseVerifier(SessionCliReleaseContract expected)
    {
        this.expected = expected;
    }

    public void DemandExact(string workspaceRoot, CliReleaseIdentity selected)
    {
        if (!string.Equals(selected.Schema, "program-kit.cli-release-identity/v1", StringComparison.Ordinal) ||
            !string.Equals(selected.CanonicalProfile, CanonicalJson.Profile, StringComparison.Ordinal) ||
            !string.Equals(selected.PackageId, expected.PackageId, StringComparison.Ordinal) ||
            !string.Equals(selected.PackageVersion, expected.PackageVersion, StringComparison.Ordinal) ||
            !string.Equals(selected.CommandName, expected.CommandName, StringComparison.Ordinal) ||
            !string.Equals(selected.ReportedVersion, expected.PackageVersion, StringComparison.Ordinal) ||
            selected.ClaimClass != ClaimClass.VerifiedEquivalent ||
            !Exact(selected.RuntimeProfile, expected.RuntimeProfile) ||
            !ExactEvidenceIdentity(selected.PackageSource))
            Fail("The selected CLI schema, package, command, reported version, runtime profile, package source, or claim class differs from the invoked release.");

        string executablePath;
        try
        {
            executablePath = LogicalPaths.ResolveInside(workspaceRoot, selected.WorkspaceRelativeExecutable);
        }
        catch (Exception exception) when (exception is ArgumentException or InvalidOperationException)
        {
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(1), OperationPhase.Validation, EffectState.None, "The selected workspace-local CLI executable path is invalid.");
        }

        if (!File.Exists(executablePath))
            Fail("The selected workspace-local CLI executable is unavailable.");
        if (!string.Equals(Digests.Sha256(File.ReadAllBytes(executablePath)), selected.ExecutableDigest, StringComparison.Ordinal))
            Fail("The selected workspace-local CLI executable digest does not match observed bytes.");

        string toolRoot = Path.GetDirectoryName(executablePath) ?? throw new InvalidDataException("The workspace-local CLI executable has no tool directory.");
        string packageName = selected.PackageId.ToLowerInvariant();
        string packagePath = Path.Combine(
            toolRoot,
            ".store",
            packageName,
            selected.PackageVersion,
            packageName,
            selected.PackageVersion,
            $"{packageName}.{selected.PackageVersion}.nupkg");
        if (!File.Exists(packagePath))
            Fail("The exact installed CLI package evidence is unavailable.");
        if (!string.Equals(Digests.Sha256(File.ReadAllBytes(packagePath)), selected.PackageDigest, StringComparison.Ordinal))
            Fail("The selected CLI package digest does not match installed package bytes.");
    }

    public static string InstalledPackagePath(string workspaceRoot, CliReleaseIdentity selected)
    {
        string executablePath = LogicalPaths.ResolveInside(workspaceRoot, selected.WorkspaceRelativeExecutable);
        string toolRoot = Path.GetDirectoryName(executablePath) ?? throw new InvalidDataException("The workspace-local CLI executable has no tool directory.");
        string packageName = selected.PackageId.ToLowerInvariant();
        return Path.Combine(toolRoot, ".store", packageName, selected.PackageVersion, packageName, selected.PackageVersion, $"{packageName}.{selected.PackageVersion}.nupkg");
    }

    private static bool ExactEvidenceIdentity(GovernedIdentity identity) =>
        !string.IsNullOrWhiteSpace(identity.Authority) &&
        !string.IsNullOrWhiteSpace(identity.Kind) &&
        !string.IsNullOrWhiteSpace(identity.Name) &&
        !string.IsNullOrWhiteSpace(identity.Revision) &&
        IsDigest(identity.Digest);

    private static bool Exact(GovernedIdentity left, GovernedIdentity right) => left == right;

    private static bool IsDigest(string value) =>
        value.Length == 71 &&
        value.StartsWith("sha256:", StringComparison.Ordinal) &&
        value[7..].All(static character => character is >= '0' and <= '9' or >= 'a' and <= 'f') &&
        !string.Equals(value, "sha256:0000000000000000000000000000000000000000000000000000000000000000", StringComparison.Ordinal);

    private static void Fail(string message) =>
        throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(1), OperationPhase.Validation, EffectState.None, message);
}
