using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Generates one exact Console host.</summary>
public sealed class ConsoleHostGenerator : IWorkbenchGenerator<DotNetHostGenerationInput>
{
    private readonly IDotNetHostGenerationCoordinator coordinator;

    /// <summary>Initializes the generator with host coordination behavior.</summary>
    public ConsoleHostGenerator(IDotNetHostGenerationCoordinator coordinator)
    {
        this.coordinator = coordinator ??
            throw new ArgumentNullException(nameof(coordinator));
    }

    /// <inheritdoc />
    public ValueTask<ImmutableArray<GeneratedOutput>> GenerateAsync(
        DotNetHostGenerationInput input,
        CancellationToken cancellationToken) =>
        coordinator.GenerateAsync(input, DotNetHostKind.Console, cancellationToken);
}
