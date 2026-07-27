namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>One explicit request-constructor mapping.</summary>
public sealed record DotNetConsoleConstructorParameter(
    [property: JsonPropertyName("position")] int Position,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("clrType")] DotNetConsoleClrTypeDescriptor ClrType,
    [property: JsonPropertyName("source")] DotNetConsoleParameterSource Source,
    [property: JsonPropertyName("defaultDisposition")]
    DotNetConsoleDefaultDisposition DefaultDisposition);
