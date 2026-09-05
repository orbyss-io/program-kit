using CShells.Features;

namespace ProgramKit.Analyzers.FeatureProbe;

/// <summary>Declares an intentionally divergent runtime feature identity.</summary>
[ShellFeature("AccessApi")]
public sealed class AccessApiFeature : IShellFeature
{
}
