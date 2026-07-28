namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>One candidate generated payload before sealing.</summary>
public sealed record GeneratedOutputPayload(
    string RelativePath,
    ReadOnlyMemory<byte> Content);
