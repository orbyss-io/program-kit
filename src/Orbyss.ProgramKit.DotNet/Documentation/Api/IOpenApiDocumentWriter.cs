namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>Projects bounded typed operation descriptors as canonical OpenAPI 3.2.0 JSON.</summary>
public interface IOpenApiDocumentWriter
{
    /// <summary>Writes one deterministic OpenAPI document.</summary>
    ReadOnlyMemory<byte> Write(OpenApiDocumentProjection document);
}
