using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Extensions;

/// <summary>Immutable exact extension registry.</summary>
/// <typeparam name="TRequest">The request contract.</typeparam>
/// <typeparam name="TResult">The result contract.</typeparam>
public sealed class WorkbenchExtensionRegistry<TRequest, TResult> :
    IWorkbenchExtensionRegistry<TRequest, TResult>
{
    private readonly ImmutableDictionary<
        ArtifactReference,
        IWorkbenchExtension<TRequest, TResult>> extensions;

    /// <summary>Initializes the registry from an explicit finite selection.</summary>
    internal WorkbenchExtensionRegistry(
        ImmutableDictionary<
            ArtifactReference,
            IWorkbenchExtension<TRequest, TResult>> extensions)
    {
        this.extensions = extensions ??
            throw new ArgumentNullException(nameof(extensions));
    }

    /// <inheritdoc />
    public WorkbenchResult<IWorkbenchExtension<TRequest, TResult>> Resolve(
        ArtifactReference extensionReference)
    {
        ArgumentNullException.ThrowIfNull(extensionReference);
        return extensions.TryGetValue(extensionReference, out var extension)
            ? new WorkbenchResult<IWorkbenchExtension<TRequest, TResult>>(
                extension,
                ProgramKitValidationResult.Valid)
            : new WorkbenchResult<IWorkbenchExtension<TRequest, TResult>>(
                default,
                ProgramKitValidationResult.From(
                [
                    WorkbenchDiagnostics.Error(
                        WorkbenchDiagnosticIds.InvalidExtensionSelection,
                        "The exact Workbench extension is not registered.",
                        "/extensionReference"),
                ]));
    }

}
