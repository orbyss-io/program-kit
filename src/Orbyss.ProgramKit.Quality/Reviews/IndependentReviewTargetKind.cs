namespace Orbyss.ProgramKit.Quality.Reviews;

/// <summary>Identifies whether independent review covers an artifact or a delta.</summary>
public enum IndependentReviewTargetKind
{
    /// <summary>Reviews one exact artifact revision.</summary>
    Artifact,
    /// <summary>Reviews the delta between two exact artifact revisions.</summary>
    Delta,
}
