using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>A versioned boundary represented in the Program Kit version topology.</summary>
public enum VersionBoundaryKind
{
    /// <summary>A semantic contract.</summary>
    Contract,

    /// <summary>A serialized wire schema.</summary>
    Schema,

    /// <summary>A package revision.</summary>
    Package,

    /// <summary>An implementation revision.</summary>
    Implementation,

    /// <summary>A code or artifact generator.</summary>
    Generator,

    /// <summary>A generated input or output.</summary>
    GeneratedArtifact,

    /// <summary>A host composition or activation boundary.</summary>
    HostComposition,

    /// <summary>A serialization profile.</summary>
    SerializationProfile,

    /// <summary>A converter contribution.</summary>
    ConverterContribution,

    /// <summary>A canonicalization profile.</summary>
    CanonicalizationProfile,

    /// <summary>A configuration contract or selection.</summary>
    Configuration,

    /// <summary>A durable Program Kit artifact.</summary>
    Artifact,

    /// <summary>Persisted data outside the artifact envelope.</summary>
    PersistedData,

    /// <summary>A command-line surface.</summary>
    CommandLine,

    /// <summary>A task definition revision.</summary>
    TaskDefinition,

    /// <summary>A task schedule revision.</summary>
    TaskSchedule,

    /// <summary>An explicitly bounded external consumer.</summary>
    ExternalConsumer,
}
