using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

[JsonSourceGenerationOptions(DefaultIgnoreCondition = JsonIgnoreCondition.Never, GenerationMode = JsonSourceGenerationMode.Metadata, NumberHandling = JsonNumberHandling.Strict, PropertyNameCaseInsensitive = false, RespectNullableAnnotations = true, RespectRequiredConstructorParameters = true, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(ProbeModel))]
internal sealed partial class ProbeJsonTestContext : JsonSerializerContext;
