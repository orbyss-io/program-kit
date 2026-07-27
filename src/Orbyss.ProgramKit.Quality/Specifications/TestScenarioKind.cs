namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Identifies the behavioral shape exercised by a scenario.</summary>
public enum TestScenarioKind
{
    /// <summary>Exercises accepted behavior.</summary>
    Positive,
    /// <summary>Exercises rejected input or behavior.</summary>
    Negative,
    /// <summary>Exercises a defined failure path.</summary>
    Failure,
    /// <summary>Exercises recovery after failure.</summary>
    Recovery,
    /// <summary>Exercises cancellation semantics.</summary>
    Cancellation,
    /// <summary>Exercises concurrent behavior.</summary>
    Concurrency,
    /// <summary>Exercises explicit migration behavior.</summary>
    Migration,
}
