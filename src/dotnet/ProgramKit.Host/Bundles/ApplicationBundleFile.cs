namespace ProgramKit.Host.Bundles;

/// <summary>Describes a digest-bound file in an application bundle.</summary>
public sealed record ApplicationBundleFile
{
    /// <summary>Gets the bundle-relative file path.</summary>
    public required string Path { get; init; }

    /// <summary>Gets the hexadecimal SHA-256 digest.</summary>
    public required string Sha256 { get; init; }
}
