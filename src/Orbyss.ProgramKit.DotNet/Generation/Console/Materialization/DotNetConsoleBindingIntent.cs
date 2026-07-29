using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Complete Console CLR binding semantics with build-derived project assembly
/// evidence omitted.
/// </summary>
public sealed record DotNetConsoleBindingIntent(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("featureType")]
    DotNetConsoleClrTypeDescriptor FeatureType,
    [property: JsonPropertyName("validationResultType")]
    DotNetConsoleClrTypeDescriptor ValidationResultType,
    [property: JsonPropertyName("operations")]
    ImmutableArray<DotNetConsoleOperationBinding> Operations);
