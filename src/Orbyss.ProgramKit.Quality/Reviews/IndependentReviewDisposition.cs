namespace Orbyss.ProgramKit.Quality.Reviews;

/// <summary>Records a reviewer's evidence-only conclusion.</summary>
public enum IndependentReviewDisposition
{
    /// <summary>The reviewer confirmed the selected claim.</summary>
    Confirmed,
    /// <summary>The reviewer recorded one or more concerns.</summary>
    ConcernRaised,
    /// <summary>The supplied evidence was insufficient for a conclusion.</summary>
    UnableToConclude,
}
