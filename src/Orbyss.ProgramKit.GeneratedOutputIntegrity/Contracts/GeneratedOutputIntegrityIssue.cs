namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>One explicit tampering diagnostic.</summary>
public sealed record GeneratedOutputIntegrityIssue(
    GeneratedOutputIntegrityIssueKind Kind,
    string Path,
    string Message);
