namespace Orbyss.ProgramKit.Development.Receipts;

/// <summary>Identifies the observed result of a human-led development capability invocation.</summary>
public enum DevelopmentResultKind
{
    /// <summary>The capability completed its bounded work.</summary>
    Completed,
    /// <summary>The capability refused work that was not eligible.</summary>
    Refused,
    /// <summary>The attempted capability work failed.</summary>
    Failed,
}
