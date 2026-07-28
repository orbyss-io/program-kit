namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Stable generated-output drift classification.</summary>
public enum GeneratedOutputIntegrityIssueKind
{
    /// <summary>A recorded generated file is absent.</summary>
    Missing,

    /// <summary>A recorded generated file has different bytes.</summary>
    Modified,

    /// <summary>An unrecorded file or directory exists in the generated root.</summary>
    Unexpected,

    /// <summary>A path, link, reparse point, or filesystem shape is unsafe.</summary>
    Unsafe,

    /// <summary>An integrity artifact is malformed or unsupported.</summary>
    Malformed,

    /// <summary>The manifest is absent or is not sealed by the external anchor.</summary>
    Unsealed,
}
