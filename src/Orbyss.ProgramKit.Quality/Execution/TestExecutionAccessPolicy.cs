using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Records the complete side-effect policy required by a specification or selected by a profile.</summary>
public sealed record TestExecutionAccessPolicy(
    NetworkAccessPolicy Network,
    ImmutableArray<string> AllowedNetworkDestinations,
    WriteAccessPolicy Writes,
    ImmutableArray<string> AllowedWriteRoots,
    RestoreAccessPolicy Restore,
    SecretAccessPolicy Secrets,
    ImmutableArray<string> AllowedSecretReferences);
