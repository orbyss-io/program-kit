using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Complete deterministic AppHost output set and tree digest.</summary>
public sealed record AspireAppHostGenerationResult(
    ImmutableArray<GeneratedOutput> Outputs,
    Sha256Digest OutputTreeSha256);
