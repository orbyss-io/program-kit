namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

internal sealed record SourceContract(
    string ValueType,
    int MaximumOccurrence,
    string? DefaultValue);
