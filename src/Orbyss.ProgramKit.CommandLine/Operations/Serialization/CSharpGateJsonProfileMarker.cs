using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

internal sealed record CSharpGateJsonProfileMarker(
    [property: JsonPropertyName("profile")] string Profile);
