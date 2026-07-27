namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>One generator-declared output below the explicit write root.</summary>
/// <param name="RelativePath">Normalized forward-slash relative path.</param>
/// <param name="Content">Complete immutable output bytes.</param>
public sealed record GeneratedOutput(
    string RelativePath,
    ReadOnlyMemory<byte> Content);
