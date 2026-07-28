namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Strict transport serializer for generation requests and refresh results.</summary>
public interface IDotNetHostRefreshSerializer
{
    /// <summary>Reads one strict generation request.</summary>
    DotNetHostGenerationRequestDocument ReadRequest(
        ReadOnlySpan<byte> content);

    /// <summary>Writes one deterministic refresh result.</summary>
    ReadOnlyMemory<byte> WriteResult(DotNetHostRefreshResult result);
}
