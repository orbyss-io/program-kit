using System.Text.Json.Serialization;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Wire input belongs to the API project.</summary>
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record LabelRequest(string Policy);
