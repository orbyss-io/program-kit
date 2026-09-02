namespace ProgramKit.Host.Bundles;

/// <summary>Describes one packaged CShells feature and its runtime closure.</summary>
public sealed record ApplicationBundleFeature
{
    /// <summary>Gets the exact CShells feature identity used in shells.json.</summary>
    public required string Identity { get; init; }

    /// <summary>Gets the NuGet package that contains the feature.</summary>
    public required string PackageId { get; init; }

    /// <summary>Gets other features that must be active in the same shell.</summary>
    public IReadOnlyList<string> FeatureDependencies { get; init; } = [];

    /// <summary>Gets runtime package identifiers required in the bundle.</summary>
    public IReadOnlyList<string> RuntimeDependencies { get; init; } = [];

    /// <summary>Gets normalized routes claimed by the feature.</summary>
    public IReadOnlyList<string> Routes { get; init; } = [];

    /// <summary>Gets whether packaging without activation is intentional.</summary>
    public bool Dormant { get; init; }
}
