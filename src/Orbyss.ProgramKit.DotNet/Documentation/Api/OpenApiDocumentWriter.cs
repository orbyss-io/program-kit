using System.Buffers;
using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>Typed OpenAPI 3.2.0 writer with no DOM-shaped public contracts.</summary>
public sealed class OpenApiDocumentWriter : IOpenApiDocumentWriter
{
    private readonly IProgramKitJsonCanonicalizer canonicalWriter;

    /// <summary>Initializes the writer with canonicalization behavior.</summary>
    public OpenApiDocumentWriter(IProgramKitJsonCanonicalizer canonicalWriter)
    {
        this.canonicalWriter = canonicalWriter ??
            throw new ArgumentNullException(nameof(canonicalWriter));
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(OpenApiDocumentProjection document)
    {
        ArgumentNullException.ThrowIfNull(document);
        var buffer = new ArrayBufferWriter<byte>();
        using (var writer = new Utf8JsonWriter(buffer))
        {
            writer.WriteStartObject();
            writer.WriteString("openapi", "3.2.0");
            writer.WriteStartObject("info");
            writer.WriteString("title", document.Title);
            writer.WriteString("version", document.ApiVersion.Value);
            writer.WriteEndObject();
            writer.WriteStartObject("components");
            writer.WriteStartObject("securitySchemes");
            foreach (var scheme in (document.SecuritySchemes.IsDefault
                         ? []
                         : document.SecuritySchemes)
                     .OrderBy(static item => item.Name, StringComparer.Ordinal))
            {
                writer.WriteStartObject(scheme.Name);
                if (scheme.Kind == OpenApiSecuritySchemeKind.OpenIdConnect)
                {
                    writer.WriteString("type", "openIdConnect");
                    writer.WriteString(
                        "openIdConnectUrl",
                        scheme.OpenIdConnectUrl!.AbsoluteUri);
                }
                else
                {
                    writer.WriteString("type", "http");
                    writer.WriteString("scheme", "bearer");
                    writer.WriteString("bearerFormat", scheme.BearerFormat);
                }

                writer.WriteEndObject();
            }

            writer.WriteEndObject();
            writer.WriteEndObject();
            writer.WriteStartArray("servers");
            foreach (var server in document.Servers.OrderBy(static item => item.Url, StringComparer.Ordinal))
            {
                writer.WriteStartObject();
                writer.WriteString("description", server.Description);
                writer.WriteString("url", server.Url);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteStartObject("paths");
            foreach (var pathGroup in document.Operations
                         .OrderBy(static item => item.Path, StringComparer.Ordinal)
                         .ThenBy(static item => item.Method, StringComparer.Ordinal)
                         .GroupBy(static item => item.Path, StringComparer.Ordinal))
            {
                writer.WriteStartObject(pathGroup.Key);
                foreach (var operation in pathGroup)
                {
                    WriteOperation(writer, operation);
                }

                writer.WriteEndObject();
            }

            writer.WriteEndObject();
            WriteProvenance(writer, document.Provenance);
            writer.WriteEndObject();
        }

        var canonical = canonicalWriter.Canonicalize(
            buffer.WrittenSpan,
            JsonSerializationLimits.Default);
        return canonical.ToArray();
    }

    private static void WriteOperation(
        Utf8JsonWriter writer,
        OpenApiOperationProjection operation)
    {
        writer.WriteStartObject(operation.Method.ToLowerInvariant());
        writer.WriteString("operationId", operation.OperationId);
        writer.WriteString("summary", operation.Summary);
        writer.WriteString("x-orbyss-operation-revision", Exact(operation.OperationRevision));
        WriteReferences(writer, "x-orbyss-input-schemas", operation.InputSchemaRevisions);
        WriteReferences(writer, "x-orbyss-result-schemas", operation.ResultSchemaRevisions);
        WriteReferences(writer, "x-orbyss-diagnostic-schemas", operation.DiagnosticSchemaRevisions);
        WriteReferences(writer, "x-orbyss-related-operations", operation.RelatedOperationRevisions);
        if (operation.Security is { } security)
        {
            writer.WriteStartArray("security");
            if (!security.Anonymous)
            {
                writer.WriteStartObject();
                foreach (var scheme in security.SchemeNames.Order(StringComparer.Ordinal))
                {
                    writer.WriteStartArray(scheme);
                    writer.WriteEndArray();
                }

                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            if (security.PolicyIdentity is { } policyIdentity)
            {
                writer.WriteString(
                    "x-orbyss-host-policy",
                    policyIdentity.Value);
            }
        }
        if (!operation.InputSchemaRevisions.IsDefaultOrEmpty)
        {
            writer.WriteStartObject("requestBody");
            writer.WriteBoolean("required", true);
            WriteJsonContent(writer, operation.InputSchemaRevisions);
            writer.WriteEndObject();
        }

        writer.WriteStartObject("responses");
        writer.WriteStartObject("200");
        writer.WriteString("description", "Operation result");
        WriteJsonContent(writer, operation.ResultSchemaRevisions);
        writer.WriteEndObject();
        if (!operation.DiagnosticSchemaRevisions.IsDefaultOrEmpty)
        {
            writer.WriteStartObject("default");
            writer.WriteString("description", "Stable operation diagnostic");
            WriteJsonContent(writer, operation.DiagnosticSchemaRevisions);
            writer.WriteEndObject();
        }

        var problemDetailsResponses = operation.ProblemDetailsResponses.IsDefault
            ? []
            : operation.ProblemDetailsResponses;
        foreach (var group in problemDetailsResponses
                     .OrderBy(static item => item.StatusCode)
                     .ThenBy(static item => item.FailureIdentity.Value, StringComparer.Ordinal)
                     .GroupBy(static item => item.StatusCode))
        {
            writer.WriteStartObject(group.Key.ToString(System.Globalization.CultureInfo.InvariantCulture));
            writer.WriteString("description", "Declared Problem Details response");
            writer.WriteStartObject("content");
            writer.WriteStartObject("application/problem+json");
            writer.WriteStartObject("schema");
            writer.WriteStartArray("oneOf");
            foreach (var response in group)
            {
                writer.WriteStartObject();
                writer.WriteString(
                    "x-orbyss-failure-identity",
                    response.FailureIdentity.Value);
                writer.WriteString(
                    "x-orbyss-problem-type",
                    response.Type.AbsoluteUri);
                writer.WriteString(
                    "x-orbyss-problem-title",
                    response.Title);
                writer.WriteString(
                    "x-orbyss-schema-revision",
                    Exact(response.ProblemSchemaRevision));
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
            writer.WriteEndObject();
            writer.WriteEndObject();
            writer.WriteEndObject();
        }

        writer.WriteEndObject();
        writer.WriteEndObject();
    }

    private static void WriteJsonContent(
        Utf8JsonWriter writer,
        ImmutableArray<ArtifactReference> schemas)
    {
        if (schemas.IsDefaultOrEmpty)
        {
            return;
        }

        writer.WriteStartObject("content");
        writer.WriteStartObject("application/json");
        writer.WriteStartObject("schema");
        writer.WriteStartArray("oneOf");
        foreach (var schema in schemas.OrderBy(static item => Exact(item), StringComparer.Ordinal))
        {
            writer.WriteStartObject();
            writer.WriteString("x-orbyss-schema-revision", Exact(schema));
            writer.WriteEndObject();
        }

        writer.WriteEndArray();
        writer.WriteEndObject();
        writer.WriteEndObject();
        writer.WriteEndObject();
    }

    private static void WriteProvenance(
        Utf8JsonWriter writer,
        IntegratorDocumentProvenance provenance)
    {
        writer.WriteStartObject("x-orbyss-provenance");
        writer.WriteString("generatorRevision", Exact(provenance.GeneratorRevision));
        writer.WriteString("shellRevision", Exact(provenance.ShellRevision));
        WriteReferences(writer, "operationRevisions", provenance.OperationRevisions);
        writer.WriteEndObject();
    }

    private static void WriteReferences(
        Utf8JsonWriter writer,
        string propertyName,
        ImmutableArray<ArtifactReference> references)
    {
        writer.WriteStartArray(propertyName);
        foreach (var reference in references.OrderBy(static item => Exact(item), StringComparer.Ordinal))
        {
            writer.WriteStringValue(Exact(reference));
        }

        writer.WriteEndArray();
    }

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
