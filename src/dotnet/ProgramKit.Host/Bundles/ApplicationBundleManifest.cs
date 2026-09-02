namespace ProgramKit.Host.Bundles;

/// <summary>Describes the immutable identity and contents of a Program Kit application bundle.</summary>
public sealed record ApplicationBundleManifest
{
    /// <summary>Gets the application-bundle schema version.</summary>
    public required int SchemaVersion { get; init; }

    /// <summary>Gets the stable application-bundle identifier.</summary>
    public required string BundleId { get; init; }

    /// <summary>Gets the application version carried by the bundle.</summary>
    public required string Version { get; init; }

    /// <summary>Gets the minimum Program Kit Host API required by the bundle.</summary>
    public required int HostApi { get; init; }

    /// <summary>Gets every file bound to the bundle manifest by digest.</summary>
    public required IReadOnlyList<ApplicationBundleFile> Files { get; init; }

    /// <summary>Gets the runtime NuGet packages carried by the bundle.</summary>
    public required IReadOnlyList<ApplicationBundlePackage> Packages { get; init; }

    /// <summary>Gets packaged application features and their activation metadata.</summary>
    public IReadOnlyList<ApplicationBundleFeature> Features { get; init; } = [];
}
