namespace Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

/// <summary>Offline metadata-inspection outcome.</summary>
public sealed record DotNetConsoleMetadataInspectionResult(
    bool IsValid,
    DotNetConsoleMetadataProof? Proof,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics);
