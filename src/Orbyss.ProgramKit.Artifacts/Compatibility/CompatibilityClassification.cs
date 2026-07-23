using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Compatibility;

/// <summary>A compatibility classification that fails closed when unknown.</summary>
public enum CompatibilityClassification
{
    /// <summary>No semantic or behavioral meaning changed.</summary>
    Editorial,

    /// <summary>The change is backward-compatible and additive.</summary>
    CompatibleAdditive,

    /// <summary>Compatibility depends on explicit conditions.</summary>
    ConditionallyCompatible,

    /// <summary>The change is incompatible.</summary>
    Breaking,

    /// <summary>Compatibility has not been established and must fail closed.</summary>
    Unknown,
}
