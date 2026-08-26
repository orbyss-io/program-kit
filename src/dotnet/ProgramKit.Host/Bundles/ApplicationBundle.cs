namespace ProgramKit.Host.Bundles;

/// <summary>Provides the verified paths, digest, and manifest for one extracted application bundle.</summary>
public sealed record ApplicationBundle
{
    /// <summary>Initializes a verified application bundle.</summary>
    /// <param name="rootPath">The extracted bundle root.</param>
    /// <param name="packagesPath">The directory containing runtime NuGet packages.</param>
    /// <param name="shellsPath">The shell-structure configuration path.</param>
    /// <param name="hostSettingsPath">The host-settings configuration path.</param>
    /// <param name="digest">The source ZIP SHA-256 digest.</param>
    /// <param name="manifest">The verified bundle manifest.</param>
    public ApplicationBundle(
        string rootPath,
        string packagesPath,
        string shellsPath,
        string hostSettingsPath,
        string digest,
        ApplicationBundleManifest manifest)
    {
        RootPath = rootPath;
        PackagesPath = packagesPath;
        ShellsPath = shellsPath;
        HostSettingsPath = hostSettingsPath;
        Digest = digest;
        Manifest = manifest;
    }

    /// <summary>Gets the extracted bundle root.</summary>
    public string RootPath { get; }

    /// <summary>Gets the directory containing runtime NuGet packages.</summary>
    public string PackagesPath { get; }

    /// <summary>Gets the shell-structure configuration path.</summary>
    public string ShellsPath { get; }

    /// <summary>Gets the host-settings configuration path.</summary>
    public string HostSettingsPath { get; }

    /// <summary>Gets the source ZIP SHA-256 digest.</summary>
    public string Digest { get; }

    /// <summary>Gets the verified bundle manifest.</summary>
    public ApplicationBundleManifest Manifest { get; }
}
