namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Exact .NET binding for one Open Console operation.</summary>
public sealed record DotNetConsoleOperationBinding(
    [property: JsonPropertyName("operationRevision")]
    ArtifactReference OperationRevision,
    [property: JsonPropertyName("generatedSymbol")] string GeneratedSymbol,
    [property: JsonPropertyName("requestType")]
    DotNetConsoleClrTypeDescriptor RequestType,
    [property: JsonPropertyName("handlerType")]
    DotNetConsoleClrTypeDescriptor HandlerType,
    [property: JsonPropertyName("validatorType")]
    DotNetConsoleClrTypeDescriptor? ValidatorType,
    [property: JsonPropertyName("constructorParameters")]
    ImmutableArray<DotNetConsoleConstructorParameter> ConstructorParameters);
