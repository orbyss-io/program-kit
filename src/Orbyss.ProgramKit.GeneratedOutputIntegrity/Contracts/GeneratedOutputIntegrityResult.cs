namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Complete deterministic result of one offline verification.</summary>
public sealed record GeneratedOutputIntegrityResult(
    ImmutableArray<GeneratedOutputIntegrityIssue> Issues)
{
    /// <summary>Whether no generated-output tampering was observed.</summary>
    public bool IsValid => Issues.IsDefaultOrEmpty;
}
