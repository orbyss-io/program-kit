namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Finite limits for one deterministic generation operation.</summary>
/// <param name="MaxFiles">Maximum number of declared outputs.</param>
/// <param name="MaxFileBytes">Maximum bytes in one output.</param>
/// <param name="MaxTotalBytes">Maximum bytes in all outputs.</param>
public sealed record GenerationLimits(
    int MaxFiles,
    long MaxFileBytes,
    long MaxTotalBytes)
{
    /// <summary>Gets conservative baseline limits.</summary>
    public static GenerationLimits Default { get; } =
        new(1_024, 16_777_216, 268_435_456);
}
