using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Json;

/// <summary>Canonicalizes model-less artifact bytes through the frozen JSON mechanics.</summary>
public sealed class NormalizeCommandOperation : ICommandOperation
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonCanonicalizer canonicalizer;

    /// <summary>Initializes the adapter with explicit file and canonicalization behavior.</summary>
    public NormalizeCommandOperation(
        ICommandFileSystem fileSystem,
        IProgramKitJsonCanonicalizer canonicalizer)
    {
        this.fileSystem = fileSystem ?? throw new ArgumentNullException(nameof(fileSystem));
        this.canonicalizer = canonicalizer ??
            throw new ArgumentNullException(nameof(canonicalizer));
    }

    /// <inheritdoc />
    public string CommandKey => "normalize";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        var source = await fileSystem.ReadAllBytesAsync(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var canonical = canonicalizer.Canonicalize(
            source.Span,
            JsonSerializationLimits.Default);
        var output = invocation.RequiredOption("output");
        if (string.Equals(output, "-", StringComparison.Ordinal))
        {
            return CommandOperationResult.Success(canonical.ToArray());
        }

        await fileSystem.WriteAllBytesAsync(
            output,
            canonical.ToArray(),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }
}
