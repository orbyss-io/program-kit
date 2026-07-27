using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;

namespace Orbyss.ProgramKit.DevContainers.Operations.Generation;

/// <summary>Generates bounded Dev Container artifacts without executing them.</summary>
public interface IDevContainerGenerator
{
    /// <summary>Generates exact files from one validated definition.</summary>
    DevContainerGenerationResult Generate(
        DevContainerDefinition definition,
        CancellationToken cancellationToken = default);
}
