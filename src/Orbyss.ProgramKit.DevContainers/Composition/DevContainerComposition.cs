using Orbyss.ProgramKit.DevContainers.Operations.Generation;
using Orbyss.ProgramKit.DevContainers.Operations.Validation;

namespace Orbyss.ProgramKit.DevContainers.Composition;

/// <summary>Explicit composition root for the deterministic Dev Container tool.</summary>
public static class DevContainerComposition
{
    /// <summary>Creates the complete fail-closed generator graph.</summary>
    public static IDevContainerGenerator CreateGenerator()
    {
        IDevContainerDefinitionValidator validator =
            new DevContainerDefinitionValidator();
        return new DevContainerGenerator(validator);
    }
}
