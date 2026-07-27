using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Default canonical document writer.</summary>
public sealed class DotNetDocumentWriter : IDotNetDocumentWriter
{
    private readonly IOpenApiDocumentWriter openApiWriter;
    private readonly IProgramKitJsonSerializer jsonSerializer;

    /// <summary>Initializes the writer with typed JSON and OpenAPI behavior.</summary>
    public DotNetDocumentWriter(
        IOpenApiDocumentWriter openApiWriter,
        IProgramKitJsonSerializer jsonSerializer)
    {
        this.openApiWriter = openApiWriter ??
            throw new ArgumentNullException(nameof(openApiWriter));
        this.jsonSerializer = jsonSerializer ??
            throw new ArgumentNullException(nameof(jsonSerializer));
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(OpenApiDocumentProjection document) =>
        openApiWriter.Write(document);

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(OpenConsoleDocument document) =>
        WriteCanonical(document);

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(OpenWorkerDocument document) =>
        WriteCanonical(document);

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(DotNetShellLockDocument document) =>
        WriteCanonical(document);

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(DotNetConsoleCommandDispatchLockDocument document) =>
        WriteCanonical(document);

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(DotNetConsoleCommandDispatchEvidenceDocument document) =>
        WriteCanonical(document);

    private ReadOnlyMemory<byte> WriteCanonical<T>(T document)
    {
        var canonical = jsonSerializer.Write(
            document,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default);
        return canonical.ToArray();
    }
}
