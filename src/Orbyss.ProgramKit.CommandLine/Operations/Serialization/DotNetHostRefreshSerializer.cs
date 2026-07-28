using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Source-generated strict JSON mechanics for generated-host refresh.</summary>
public sealed class DotNetHostRefreshSerializer :
    IDotNetHostRefreshSerializer
{
    /// <inheritdoc />
    public DotNetHostGenerationRequestDocument ReadRequest(
        ReadOnlySpan<byte> content) =>
        JsonSerializer.Deserialize(
            content,
            DotNetHostRefreshJsonContext.Default
                .DotNetHostGenerationRequestDocument) ??
        throw new JsonException("The generation request is empty.");

    /// <inheritdoc />
    public ReadOnlyMemory<byte> WriteResult(DotNetHostRefreshResult result)
    {
        ArgumentNullException.ThrowIfNull(result);
        return JsonSerializer.SerializeToUtf8Bytes(
            result,
            DotNetHostRefreshJsonContext.Default.DotNetHostRefreshResult);
    }
}
