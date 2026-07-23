namespace Orbyss.ProgramKit.Quality.Evidence;

/// <summary>Identifies the outcome recorded by test evidence.</summary>
public enum TestEvidenceOutcome
{
    /// <summary>The expected result was observed.</summary>
    Passed,
    /// <summary>The expected result was not observed.</summary>
    Failed,
    /// <summary>The evidence cannot establish pass or failure.</summary>
    Inconclusive,
}
