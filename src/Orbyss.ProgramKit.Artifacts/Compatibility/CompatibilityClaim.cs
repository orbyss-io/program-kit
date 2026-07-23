using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Compatibility;

/// <summary>Classifies one compatibility dimension.</summary>
/// <param name="Dimension">The independent compatibility dimension.</param>
/// <param name="Classification">The compatibility classification.</param>
/// <param name="Conditions">Explicit conditions for a conditional classification.</param>
public sealed record CompatibilityClaim(
    CompatibilityDimension Dimension,
    CompatibilityClassification Classification,
    ImmutableArray<string> Conditions);
