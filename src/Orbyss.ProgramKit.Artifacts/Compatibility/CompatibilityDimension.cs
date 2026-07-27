using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Compatibility;

/// <summary>A dimension on which compatibility is classified independently.</summary>
public enum CompatibilityDimension
{
    /// <summary>Domain or application behavior.</summary>
    SemanticBehavior,

    /// <summary>Ability to read existing wire representations.</summary>
    WireRead,

    /// <summary>Wire representations emitted by the writer.</summary>
    WireWrite,

    /// <summary>Source-level API compatibility.</summary>
    SourceApi,

    /// <summary>Binary ABI compatibility.</summary>
    BinaryAbi,

    /// <summary>Configuration compatibility.</summary>
    Configuration,

    /// <summary>Persisted artifact or data compatibility.</summary>
    PersistedArtifacts,

    /// <summary>Generated input or output compatibility.</summary>
    GeneratedArtifacts,

    /// <summary>Command-line surface compatibility.</summary>
    CommandLine,

    /// <summary>Host composition and activation compatibility.</summary>
    HostComposition,
}
