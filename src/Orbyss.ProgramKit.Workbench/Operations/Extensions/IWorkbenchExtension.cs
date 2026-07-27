namespace Orbyss.ProgramKit.Workbench.Operations.Extensions;

/// <summary>One explicitly selected deterministic Workbench extension.</summary>
/// <typeparam name="TRequest">The request contract.</typeparam>
/// <typeparam name="TResult">The result contract.</typeparam>
public interface IWorkbenchExtension<in TRequest, out TResult>
{
    /// <summary>Gets the exact extension descriptor.</summary>
    WorkbenchExtensionDescriptor Descriptor { get; }

    /// <summary>Executes the operation without ambient discovery.</summary>
    TResult Execute(TRequest request, CancellationToken cancellationToken);
}
