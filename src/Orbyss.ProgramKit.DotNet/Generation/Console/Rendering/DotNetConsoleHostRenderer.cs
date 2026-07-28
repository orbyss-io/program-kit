using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;

internal sealed class DotNetConsoleHostRenderer
{
    private readonly ImmutableArray<IDotNetConsoleOutputRenderer> renderers;

    internal DotNetConsoleHostRenderer(
        ImmutableArray<IDotNetConsoleOutputRenderer> renderers)
    {
        if (renderers.IsDefaultOrEmpty)
        {
            throw new ArgumentException(
                "At least one Console output renderer is required.",
                nameof(renderers));
        }

        this.renderers = renderers;
    }

    internal ImmutableArray<GeneratedOutput> Render(
        DotNetConsoleHostProjection projection)
    {
        var outputs = renderers
            .SelectMany(renderer => renderer.Render(projection))
            .OrderBy(static output => output.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        if (outputs.Select(static output => output.RelativePath)
            .Distinct(StringComparer.Ordinal)
            .Count() != outputs.Length)
        {
            throw new InvalidOperationException(
                "Console renderers produced duplicate output paths.");
        }

        return outputs;
    }
}
