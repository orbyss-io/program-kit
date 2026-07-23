namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Generation.TestSupport;

internal sealed class TestWorkbenchGenerator : IWorkbenchGenerator<string>
{
    private readonly ImmutableArray<GeneratedOutput> outputs;

    internal TestWorkbenchGenerator(ImmutableArray<GeneratedOutput> outputs)
    {
        this.outputs = outputs;
    }

    public ValueTask<ImmutableArray<GeneratedOutput>> GenerateAsync(
        string input,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult(outputs);
}
