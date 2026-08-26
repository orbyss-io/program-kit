namespace ProgramKit.Host.Bundles;

/// <summary>Describes a runtime NuGet package carried by an application bundle.</summary>
public sealed record ApplicationBundlePackage
{
    /// <summary>Gets the NuGet package identifier.</summary>
    public required string Id { get; init; }

    /// <summary>Gets the exact NuGet package version.</summary>
    public required string Version { get; init; }

    /// <summary>Gets the bundle-relative package path.</summary>
    public required string Path { get; init; }

    /// <summary>Gets the package SHA-256 digest.</summary>
    public required string Sha256 { get; init; }
}
