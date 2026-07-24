using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Coordinates validated deterministic generation for one required host kind.</summary>
public interface IDotNetHostGenerationCoordinator
{
    /// <summary>Generates exactly one selected host.</summary>
    ValueTask<ImmutableArray<GeneratedOutput>> GenerateAsync(
        DotNetHostGenerationInput input,
        DotNetHostKind requiredKind,
        CancellationToken cancellationToken);
}
