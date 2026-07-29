using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Artifacts;

/// <summary>
/// Identifies and validates one explicit artifact without changing its bytes.
/// </summary>
public sealed class ArtifactInspectCommandOperation : ICommandOperation
{
    private static readonly UTF8Encoding Utf8 = new(false);
    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandSchemaSelector schemaSelector;
    private readonly IWorkbenchSchemaValidator validator;
    private readonly IConsumerCapabilityPayload capabilityPayload;

    /// <summary>Initializes the explicit read-only inspection edges.</summary>
    public ArtifactInspectCommandOperation(
        ICommandFileSystem fileSystem,
        ICommandSchemaSelector schemaSelector,
        IWorkbenchSchemaValidator validator,
        IConsumerCapabilityPayload capabilityPayload)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.schemaSelector = schemaSelector ??
            throw new ArgumentNullException(nameof(schemaSelector));
        this.validator = validator ??
            throw new ArgumentNullException(nameof(validator));
        this.capabilityPayload = capabilityPayload ??
            throw new ArgumentNullException(nameof(capabilityPayload));
    }

    /// <inheritdoc />
    public string CommandKey => "artifacts.inspect";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        var path = invocation.Arguments[0];
        var content = await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
        var explicitSchema = invocation.OptionalOption("schema");
        Orbyss.ProgramKit.Artifacts.References.ArtifactReference schema;
        var module = explicitSchema is null
            ? schemaSelector.Resolve(content, out schema)
            : schemaSelector.Resolve(explicitSchema, out schema);
        var validation = validator.Validate(
            content,
            module,
            schema,
            JsonSerializationLimits.Default);
        var exactSchema = string.Concat(
            schema.Identity.Value,
            "@",
            schema.Version.Value);
        var owners = capabilityPayload.Catalog
            .Where(entry => entry.Schemas.Contains(
                exactSchema,
                StringComparer.Ordinal))
            .Select(static entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var (declaredIdentity, declaredVersion) =
            ReadIdentityAndVersion(content.Span);
        var identity = declaredIdentity ?? "unavailable";
        var version = declaredVersion ?? "unavailable";
        var digest = string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content.Span))
                .ToLowerInvariant());
        var format = invocation.OptionalOption("format") ?? "text";
        var output = string.Equals(format, "json", StringComparison.Ordinal)
            ? RenderJson(
                path,
                identity,
                version,
                digest,
                exactSchema,
                schema.Digest.Value,
                validation.IsValid,
                owners,
                validation.Diagnostics)
            : RenderText(
                path,
                identity,
                version,
                digest,
                exactSchema,
                schema.Digest.Value,
                validation.IsValid,
                owners,
                validation.Diagnostics);
        return CommandOperationResult.Success(output);
    }

    private static (string? Identity, string? Version)
        ReadIdentityAndVersion(ReadOnlySpan<byte> content)
    {
        try
        {
            var reader = new Utf8JsonReader(
                content,
                new JsonReaderOptions
                {
                    AllowTrailingCommas = false,
                    CommentHandling = JsonCommentHandling.Disallow,
                    MaxDepth = 128,
                });
            if (!reader.Read() ||
                reader.TokenType != JsonTokenType.StartObject)
            {
                return (null, null);
            }

            string? identity = null;
            string? version = null;
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndObject)
            {
                if (reader.TokenType != JsonTokenType.PropertyName)
                {
                    return (null, null);
                }

                var property = reader.GetString();
                if (!reader.Read())
                {
                    return (null, null);
                }

                if (string.Equals(
                        property,
                        "identity",
                        StringComparison.Ordinal) &&
                    reader.TokenType == JsonTokenType.String)
                {
                    identity = reader.GetString();
                }
                else if (string.Equals(
                             property,
                             "version",
                             StringComparison.Ordinal) &&
                         reader.TokenType == JsonTokenType.String)
                {
                    version = reader.GetString();
                }

                reader.Skip();
            }

            return (identity, version);
        }
        catch (JsonException)
        {
            return (null, null);
        }
    }

    private static byte[] RenderText(
        string path,
        string identity,
        string version,
        string digest,
        string schema,
        string schemaDigest,
        bool valid,
        string[] owners,
        IEnumerable<Orbyss.ProgramKit.Artifacts.Diagnostics.ProgramKitDiagnostic>
            diagnostics)
    {
        StringBuilder output = new();
        output.Append("Artifact: ")
            .AppendLine(Path.GetFullPath(path))
            .Append("Identity: ")
            .Append(identity)
            .Append('@')
            .AppendLine(version)
            .Append("Raw SHA-256: ")
            .AppendLine(digest)
            .Append("Schema: ")
            .Append(schema)
            .Append(" # ")
            .AppendLine(schemaDigest)
            .Append("Valid: ")
            .AppendLine(valid ? "yes" : "no")
            .Append("Owning capabilities: ")
            .AppendLine(owners.Length == 0
                ? "none registered"
                : string.Join(", ", owners))
            .AppendLine("Related command: validate");
        foreach (var diagnostic in diagnostics)
        {
            output.Append(diagnostic.Id)
                .Append(' ')
                .Append(diagnostic.Path)
                .Append(": ")
                .AppendLine(diagnostic.Message);
        }

        return Utf8.GetBytes(output.ToString());
    }

    private static byte[] RenderJson(
        string path,
        string identity,
        string version,
        string digest,
        string schema,
        string schemaDigest,
        bool valid,
        string[] owners,
        IEnumerable<Orbyss.ProgramKit.Artifacts.Diagnostics.ProgramKitDiagnostic>
            diagnostics)
    {
        using MemoryStream output = new();
        using (Utf8JsonWriter writer = new(output))
        {
            writer.WriteStartObject();
            writer.WriteString("artifactPath", Path.GetFullPath(path));
            writer.WriteStartArray("capabilityOwners");
            foreach (var owner in owners)
            {
                writer.WriteStringValue(owner);
            }

            writer.WriteEndArray();
            writer.WriteStartArray("diagnostics");
            foreach (var diagnostic in diagnostics)
            {
                writer.WriteStartObject();
                writer.WriteString("id", diagnostic.Id);
                writer.WriteString("message", diagnostic.Message);
                writer.WriteString("path", diagnostic.Path);
                writer.WriteString(
                    "severity",
                    diagnostic.Severity.ToString().ToLowerInvariant());
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteString("identity", identity);
            writer.WriteString("rawSha256", digest);
            writer.WriteString("relatedCommand", "validate");
            writer.WriteString("schema", schema);
            writer.WriteString("schemaSha256", schemaDigest);
            writer.WriteBoolean("valid", valid);
            writer.WriteString("version", version);
            writer.WriteEndObject();
        }

        return output.ToArray();
    }
}
