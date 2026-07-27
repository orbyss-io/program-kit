namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Evidence returned only after all declared outputs commit atomically.</summary>
/// <param name="Outputs">Published outputs in deterministic path order.</param>
public sealed record GenerationReceipt(
    ImmutableArray<GeneratedOutputReceipt> Outputs);
