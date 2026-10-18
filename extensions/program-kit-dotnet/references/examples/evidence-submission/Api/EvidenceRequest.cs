using System.Text.Json.Serialization;

namespace ProgramKit.Examples.Evidence;

/// <summary>Strict wire input, distinct from Core admission and provider JSON.</summary>
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record EvidenceRequest(
    string Title,
    string Date,
    string Content
);
