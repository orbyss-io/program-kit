namespace Orbyss.ProgramKit.UnitTests.Workbench.Composition.Extensions.TestSupport;

internal sealed class TestWorkbenchExtension : IWorkbenchExtension<string, string>
{
    internal TestWorkbenchExtension(WorkbenchExtensionDescriptor descriptor)
    {
        Descriptor = descriptor ??
            throw new ArgumentNullException(nameof(descriptor));
    }

    public WorkbenchExtensionDescriptor Descriptor { get; }

    public string Execute(
        string request,
        CancellationToken cancellationToken) =>
        request;
}
