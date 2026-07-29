using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Readiness;

/// <summary>Internal complete-workspace setup verification result.</summary>
internal sealed record WorkspaceSetup(
    bool Ready,
    string Reason,
    ImmutableArray<string> Providers)
{
    /// <summary>Creates one fail-closed setup result.</summary>
    internal static WorkspaceSetup Blocked(
        string reason,
        ImmutableArray<string> providers = default) =>
        new(false, reason, providers.IsDefault ? [] : providers);

    /// <summary>Creates one fully verified setup result.</summary>
    internal static WorkspaceSetup Verified(
        ImmutableArray<string> providers) =>
        new(true, string.Empty, providers);
}
