using Microsoft.AspNetCore.OpenApi;
using Microsoft.OpenApi;

namespace Numeric.Contract.Api;

/// <summary>Intentionally claims numeric strings for a strict fixture contract; never a production repair.</summary>
public sealed class IntentionallyMalformedNumericSchemaTransformer : IOpenApiSchemaTransformer
{
    /// <inheritdoc />
    public Task TransformAsync(
        OpenApiSchema schema,
        OpenApiSchemaTransformerContext context,
        CancellationToken cancellationToken
    )
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (context.JsonTypeInfo.Type != typeof(ScopedNullableNumericRequest))
            return Task.CompletedTask;
        if (schema.Properties is null || !schema.Properties.TryGetValue("optionalCount", out var declared)
            || declared is not OpenApiSchema numeric)
            throw new InvalidOperationException("Intentionally malformed fixture could not find its owned nullable numeric property.");

        numeric.Type = JsonSchemaType.Integer | JsonSchemaType.String | JsonSchemaType.Null;

        return Task.CompletedTask;
    }
}
