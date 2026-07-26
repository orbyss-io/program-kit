namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Exact identity and version of one registered Aspire integration.</summary>
public sealed record AspireIntegrationSelection(
    ProgramKitIdentifier Identity,
    SemanticVersion Version);
