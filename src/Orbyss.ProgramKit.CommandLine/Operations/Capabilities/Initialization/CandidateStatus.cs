namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Internal planned wrapper transaction state.</summary>
internal enum CandidateStatus
{
    /// <summary>The output does not yet exist.</summary>
    Created,

    /// <summary>The exact previously owned bytes will be refreshed.</summary>
    Updated,

    /// <summary>The output already equals the desired bytes.</summary>
    Unchanged,
}
