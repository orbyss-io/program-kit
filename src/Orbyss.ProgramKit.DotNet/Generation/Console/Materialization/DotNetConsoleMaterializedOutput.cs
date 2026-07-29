namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>One exact Program Kit-owned output bound by the lock.</summary>
public sealed record DotNetConsoleMaterializedOutput(
    [property: JsonPropertyName("relativePath")] string RelativePath,
    [property: JsonPropertyName("digest")] Sha256Digest Digest);
