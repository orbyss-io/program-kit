using Orbyss.ProgramKit.Workbench.Operations.Extensions;

namespace Orbyss.ProgramKit.Workbench.Composition.Extensions;

/// <summary>Builds exact registries from uncollapsed finite registration sequences.</summary>
public interface IWorkbenchExtensionRegistryFactory
{
    /// <summary>
    /// Validates duplicate and conflicting semantic revisions before creating
    /// an immutable exact registry.
    /// </summary>
    WorkbenchResult<IWorkbenchExtensionRegistry<TRequest, TResult>> Create<TRequest, TResult>(
        IEnumerable<IWorkbenchExtension<TRequest, TResult>> extensions);
}
