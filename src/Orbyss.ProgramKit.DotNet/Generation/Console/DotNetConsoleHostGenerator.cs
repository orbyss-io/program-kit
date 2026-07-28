using System.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;
using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;
using Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console;

internal sealed class DotNetConsoleHostGenerator :
    IDotNetConsoleHostGenerator
{
    private readonly IDotNetConsoleBindingValidator bindingValidator;
    private readonly IDotNetConsoleMetadataInspector metadataInspector;
    private readonly IDotNetConsoleProjectionCompiler projectionCompiler;
    private readonly DotNetConsoleHostRenderer renderer;
    private readonly IDotNetConsoleCandidateCompiler candidateCompiler;

    internal DotNetConsoleHostGenerator(
        IDotNetConsoleBindingValidator bindingValidator,
        IDotNetConsoleMetadataInspector metadataInspector,
        IDotNetConsoleProjectionCompiler projectionCompiler,
        DotNetConsoleHostRenderer renderer,
        IDotNetConsoleCandidateCompiler candidateCompiler)
    {
        this.bindingValidator = bindingValidator ??
            throw new ArgumentNullException(nameof(bindingValidator));
        this.metadataInspector = metadataInspector ??
            throw new ArgumentNullException(nameof(metadataInspector));
        this.projectionCompiler = projectionCompiler ??
            throw new ArgumentNullException(nameof(projectionCompiler));
        this.renderer = renderer ??
            throw new ArgumentNullException(nameof(renderer));
        this.candidateCompiler = candidateCompiler ??
            throw new ArgumentNullException(nameof(candidateCompiler));
    }

    public ImmutableArray<GeneratedOutput> Generate(
        DotNetHostDefinition host,
        DotNetHostLock hostLock,
        OpenConsoleDocument document,
        DotNetConsoleGenerationInput input,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(host);
        ArgumentNullException.ThrowIfNull(hostLock);
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(input);
        cancellationToken.ThrowIfCancellationRequested();
        if (host.Kind != DotNetHostKind.Console ||
            hostLock.Kind != DotNetHostKind.Console)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidHostSelection,
                "Typed Console generation requires an exact Console host and lock.",
                "/host");
        }

        var bindingValidation = bindingValidator.Validate(
            input.Binding,
            document);
        if (!bindingValidation.IsValid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidConsoleBinding,
                "Typed Console generation requires a valid exact binding document.",
                "/consoleGeneration/binding");
        }

        var metadata = metadataInspector.Inspect(
            input.Binding,
            input.ConsumerReferenceAssemblyPath);
        if (!metadata.IsValid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.ConsoleMetadataMismatch,
                "The exact consumer reference assembly does not satisfy the Console binding.",
                "/consoleGeneration/consumerReferenceAssemblyPath");
        }

        var projection = projectionCompiler.Compile(
            document,
            input.Binding);
        if (!projection.IsValid || projection.Projection is null)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.ConsoleProjectionFailed,
                "The accepted Console contracts cannot be projected into the pinned Spectre host profile.",
                "/consoleGeneration");
        }

        var outputs = renderer.Render(projection.Projection);
        var sources = outputs
            .Where(static output =>
                output.RelativePath.EndsWith(
                    ".cs",
                    StringComparison.Ordinal))
            .Select(static output => new DotNetConsoleSourceFile(
                output.RelativePath,
                Encoding.UTF8.GetString(output.Content.Span)))
            .ToImmutableArray();
        var compilation = candidateCompiler.Compile(
            sources,
            input.CompilationReferences,
            cancellationToken);
        if (!compilation.IsValid)
        {
            var detail = compilation.Diagnostics.IsDefaultOrEmpty
                ? "No compiler diagnostic was available."
                : string.Join(
                    " | ",
                    compilation.Diagnostics.Select(static diagnostic =>
                        string.Concat(
                            diagnostic.Path,
                            ": ",
                            diagnostic.Message)));
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.ConsoleCandidateCompilationFailed,
                string.Concat(
                    "The generated typed Console host candidate does not compile against its exact references. ",
                    detail),
                "/consoleGeneration/compilationReferences");
        }

        return outputs;
    }
}
