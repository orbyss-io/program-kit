using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

[JsonSourceGenerationOptions(DefaultIgnoreCondition = JsonIgnoreCondition.Never, GenerationMode = JsonSourceGenerationMode.Metadata, NumberHandling = JsonNumberHandling.Strict, PropertyNameCaseInsensitive = false, PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase, RespectNullableAnnotations = true, RespectRequiredConstructorParameters = true, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(ContextOptionsModel))]
internal sealed partial class MismatchedOptionsJsonContext : JsonSerializerContext;
