namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>One finite repository-relative scaffold output and its bytes.</summary>
public sealed record ConsumerAnalyzerScaffoldFile(
    string RelativePath,
    ReadOnlyMemory<byte> Content);
