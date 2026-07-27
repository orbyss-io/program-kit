using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;
using Orbyss.ProgramKit.Workbench.Operations.Extensions;

namespace Orbyss.ProgramKit.Workbench.Composition.Extensions;

/// <summary>Default fail-closed exact extension registry factory.</summary>
public sealed class WorkbenchExtensionRegistryFactory :
    IWorkbenchExtensionRegistryFactory
{
    /// <inheritdoc />
    public WorkbenchResult<IWorkbenchExtensionRegistry<TRequest, TResult>> Create<TRequest, TResult>(
        IEnumerable<IWorkbenchExtension<TRequest, TResult>> extensions)
    {
        ArgumentNullException.ThrowIfNull(extensions);
        var exact = ImmutableDictionary.CreateBuilder<
            ArtifactReference,
            IWorkbenchExtension<TRequest, TResult>>();
        var revisions = new Dictionary<string, Sha256Digest>(StringComparer.Ordinal);
        foreach (var extension in extensions)
        {
            if (extension is null)
            {
                return Failure<TRequest, TResult>(
                    "An extension registration cannot be null.");
            }

            var descriptor = extension.Descriptor;
            if (descriptor is null ||
                !exact.TryAdd(descriptor.Reference, extension))
            {
                return Failure<TRequest, TResult>(
                    "Duplicate exact Workbench extension registrations are forbidden.");
            }

            var revisionKey = string.Concat(
                descriptor.Identity.Value,
                "@",
                descriptor.Version.Value);
            if (revisions.TryGetValue(revisionKey, out var digest) &&
                digest != descriptor.Digest)
            {
                return Failure<TRequest, TResult>(
                    "One extension identity and version cannot resolve to conflicting digests.");
            }

            revisions[revisionKey] = descriptor.Digest;
        }

        IWorkbenchExtensionRegistry<TRequest, TResult> registry =
            new WorkbenchExtensionRegistry<TRequest, TResult>(exact.ToImmutable());
        return new WorkbenchResult<IWorkbenchExtensionRegistry<TRequest, TResult>>(
            registry,
            ProgramKitValidationResult.Valid);
    }

    private static WorkbenchResult<IWorkbenchExtensionRegistry<TRequest, TResult>>
        Failure<TRequest, TResult>(string message) =>
        new(
            default,
            ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidExtensionSelection,
                    message,
                    "/extensions"),
            ]));
}
