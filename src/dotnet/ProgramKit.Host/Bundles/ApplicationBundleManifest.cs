namespace ProgramKit.Host.Bundles;

public sealed record ApplicationBundleManifest
{
    public required int SchemaVersion { get; init; }

    public required string BundleId { get; init; }

    public required string Version { get; init; }

    public required int HostApi { get; init; }

    public required IReadOnlyList<ApplicationBundleFile> Files { get; init; }

    public required IReadOnlyList<ApplicationBundlePackage> Packages { get; init; }
}

public sealed record ApplicationBundleFile
{
    public required string Path { get; init; }

    public required string Sha256 { get; init; }
}

public sealed record ApplicationBundlePackage
{
    public required string Id { get; init; }

    public required string Version { get; init; }

    public required string Path { get; init; }

    public required string Sha256 { get; init; }
}
