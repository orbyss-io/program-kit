namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>One finite Open Console logical-type to CLR-scalar mapping.</summary>
public sealed record DotNetConsoleLogicalClrType(
    [property: JsonPropertyName("logicalType")] string LogicalType,
    [property: JsonPropertyName("scalarMetadataName")]
    string ScalarMetadataName);
