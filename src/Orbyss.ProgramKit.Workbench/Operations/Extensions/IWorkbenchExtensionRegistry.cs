namespace Orbyss.ProgramKit.Workbench.Operations.Extensions;

/// <summary>Resolves exact in-process extensions without assembly scanning.</summary>
/// <typeparam name="TRequest">The request contract.</typeparam>
/// <typeparam name="TResult">The result contract.</typeparam>
public interface IWorkbenchExtensionRegistry<TRequest, TResult>
{
    /// <summary>Resolves one exact selected extension.</summary>
    WorkbenchResult<IWorkbenchExtension<TRequest, TResult>> Resolve(
        ArtifactReference extensionReference);
}
