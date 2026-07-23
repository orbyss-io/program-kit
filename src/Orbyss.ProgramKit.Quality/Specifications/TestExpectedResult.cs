namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Defines the expected overall result of a test specification.</summary>
public sealed record TestExpectedResult(
    string OutcomeCode,
    string Description);
