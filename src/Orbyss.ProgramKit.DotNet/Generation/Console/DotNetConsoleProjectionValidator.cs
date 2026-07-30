using Orbyss.ProgramKit.DotNet.Operations;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console;

/// <summary>
/// Verifies one Open Console document against its exact shell, host, generator,
/// operation, and typed-contract projection.
/// </summary>
public static class DotNetConsoleProjectionValidator
{
    /// <summary>
    /// Determines whether alpha.2 commands declare exactly the schema sets
    /// owned by one selected shell host.
    /// </summary>
    public static bool IsExactAlpha2(
        DotNetHostDefinition host,
        ImmutableArray<OpenConsoleCommandAlpha2> commands)
    {
        ArgumentNullException.ThrowIfNull(host);
        if (commands.IsDefault ||
            host.OperationBindings.Length != commands.Length)
        {
            return false;
        }

        foreach (var command in commands)
        {
            var matches = host.OperationBindings
                .Where(binding =>
                    binding.OperationContract.OperationRevision ==
                        command.OperationRevision)
                .ToArray();
            if (matches.Length != 1 ||
                !ExactDeclaredSet(
                    matches[0].GetInputSchemaRevisions(),
                    command.RequestSchemaRevisions) ||
                !ExactDeclaredSet(
                    matches[0].GetResultSchemaRevisions(),
                    command.ResultSchemaRevisions) ||
                !ExactDeclaredSet(
                    matches[0].GetDiagnosticSchemaRevisions(),
                    command.DiagnosticSchemaRevisions))
            {
                return false;
            }
        }

        return true;
    }

    /// <summary>Determines whether the document is the host's exact projection.</summary>
    public static bool IsExact(
        ArtifactReference shellRevision,
        DotNetHostDefinition host,
        OpenConsoleDocument document)
    {
        ArgumentNullException.ThrowIfNull(shellRevision);
        ArgumentNullException.ThrowIfNull(host);
        ArgumentNullException.ThrowIfNull(document);
        if (document.Provenance.ShellRevision != shellRevision ||
            document.Provenance.GeneratorRevision !=
                host.GeneratorProfileRevision ||
            document.HostRevision.Identity != host.Identity ||
            document.HostRevision.Version != host.Version)
        {
            return false;
        }

        var bindingKeys = host.OperationBindings
            .Select(static binding =>
                Exact(binding.OperationContract.OperationRevision))
            .ToHashSet(StringComparer.Ordinal);
        var provenanceKeys = document.Provenance.OperationRevisions
            .Select(Exact)
            .ToHashSet(StringComparer.Ordinal);
        if (!bindingKeys.SetEquals(provenanceKeys) ||
            host.OperationBindings.Length != document.Commands.Length)
        {
            return false;
        }

        foreach (var command in document.Commands)
        {
            var matches = host.OperationBindings
                .Where(binding =>
                    binding.OperationContract.OperationRevision ==
                        command.OperationRevision)
                .ToArray();
            var inputSchemas = command.Arguments
                .Select(static argument => argument.ValueSchemaRevision)
                .Concat(
                    document.GlobalOptions
                        .Concat(command.Options)
                        .Where(static option =>
                            option.ValueSchemaRevision is not null)
                        .Select(static option =>
                            option.ValueSchemaRevision!))
                .Concat(command.StandardInput is null
                    ? []
                    : [command.StandardInput.SchemaRevision]);
            var diagnosticSchemas = command.ExitCodes
                .SelectMany(static exitCode =>
                    exitCode.DiagnosticSchemaRevisions)
                .Concat(command.StandardError is null
                    ? []
                    : [command.StandardError.SchemaRevision]);
            if (matches.Length != 1 ||
                !ExactDeclaredSet(
                    matches[0].GetInputSchemaRevisions(),
                    inputSchemas) ||
                !ContainsOrAbsent(
                    matches[0].GetResultSchemaRevisions(),
                    command.StandardOutput) ||
                !ExactDeclaredSet(
                    matches[0].GetDiagnosticSchemaRevisions(),
                    diagnosticSchemas))
            {
                return false;
            }
        }

        return true;
    }

    private static bool ContainsOrAbsent(
        ImmutableArray<ArtifactReference> references,
        OpenConsoleStreamContract? stream) =>
        stream is null || references.Contains(stream.SchemaRevision);

    private static bool ExactDeclaredSet(
        ImmutableArray<ArtifactReference> expected,
        IEnumerable<ArtifactReference> declared)
    {
        var expectedKeys = expected
            .Select(Exact)
            .ToHashSet(StringComparer.Ordinal);
        return expectedKeys.SetEquals(declared.Select(Exact));
    }

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
