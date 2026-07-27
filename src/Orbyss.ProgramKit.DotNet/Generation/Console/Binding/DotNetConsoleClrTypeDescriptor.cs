namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Structured, non-executable description of one closed CLR type.</summary>
public sealed record DotNetConsoleClrTypeDescriptor(
    [property: JsonPropertyName("metadataName")] string MetadataName,
    [property: JsonPropertyName("genericArguments")]
    ImmutableArray<DotNetConsoleClrTypeDescriptor> GenericArguments,
    [property: JsonPropertyName("referenceNullability")]
    DotNetConsoleReferenceNullability ReferenceNullability);
