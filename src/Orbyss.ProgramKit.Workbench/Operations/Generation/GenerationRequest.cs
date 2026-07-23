namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Explicit input and publication bounds for one generation operation.</summary>
/// <typeparam name="T">The generator input type.</typeparam>
/// <param name="Input">Validated structured generator input.</param>
/// <param name="WriteRoot">Explicit output root interpreted by the workspace.</param>
/// <param name="CollisionPolicy">Declared collision behavior.</param>
/// <param name="Limits">Finite operation limits.</param>
public sealed record GenerationRequest<T>(
    T Input,
    string WriteRoot,
    GenerationCollisionPolicy CollisionPolicy,
    GenerationLimits Limits);
