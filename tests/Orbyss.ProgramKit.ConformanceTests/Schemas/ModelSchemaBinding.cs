namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

internal sealed record ModelSchemaBinding(
    Type ModelType,
    string SchemaSuffix,
    string[] Pointer);
