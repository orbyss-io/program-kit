using System.Text;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Json;

/// <summary>Calculates the digest of canonical model-less artifact bytes.</summary>
public sealed class DigestCommandOperation : ICommandOperation
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonCanonicalizer canonicalizer;

    /// <summary>Initializes the adapter with explicit file and canonicalization behavior.</summary>
    public DigestCommandOperation(
        ICommandFileSystem fileSystem,
        IProgramKitJsonCanonicalizer canonicalizer)
    {
        this.fileSystem = fileSystem ?? throw new ArgumentNullException(nameof(fileSystem));
        this.canonicalizer = canonicalizer ??
            throw new ArgumentNullException(nameof(canonicalizer));
    }

    /// <inheritdoc />
    public string CommandKey => "digest";

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
        return CommandOperationResult.Success(
            Encoding.UTF8.GetBytes(string.Concat(canonical.Digest.Value, Environment.NewLine)));
    }
}
