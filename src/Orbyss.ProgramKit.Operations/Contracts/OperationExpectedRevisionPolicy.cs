namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Whether invocation mechanics carry an expected revision.</summary>
public enum OperationExpectedRevisionPolicy
{
    /// <summary>No expected revision is carried.</summary>
    Unsupported,

    /// <summary>An expected revision may be carried.</summary>
    Optional,

    /// <summary>An expected revision must be carried.</summary>
    Required,
}
