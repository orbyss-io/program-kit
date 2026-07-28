namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Deterministic refresh disposition over one exact generated host.</summary>
public sealed record DotNetHostRefreshResult(
    string Action,
    string OutputRoot,
    string CandidateManifestSha256,
    string CurrentState,
    string? QuarantineDigest);
