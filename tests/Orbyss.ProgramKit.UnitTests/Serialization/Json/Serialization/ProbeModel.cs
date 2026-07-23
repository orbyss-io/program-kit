using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed record ProbeModel([property: JsonPropertyName("z")] string Z, [property: JsonPropertyName("a")] int A, [property: JsonPropertyName("id")] ProbeId Id);
