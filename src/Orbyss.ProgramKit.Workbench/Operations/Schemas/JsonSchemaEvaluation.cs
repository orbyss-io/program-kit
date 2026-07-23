namespace Orbyss.ProgramKit.Workbench.Operations.Schemas;

internal sealed record JsonSchemaEvaluation(
    bool IsValid,
    ImmutableArray<string> InvalidLocations);
