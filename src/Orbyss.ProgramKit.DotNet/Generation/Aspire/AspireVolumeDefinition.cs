namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>One explicit named container volume; host bind mounts are not inferred.</summary>
public sealed record AspireVolumeDefinition(
    string ResourceName,
    string Name,
    string TargetPath,
    bool IsReadOnly);
