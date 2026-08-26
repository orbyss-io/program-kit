namespace ProgramKit.Host.Bundles;

public sealed record ApplicationBundle(
    string RootPath,
    string PackagesPath,
    string ShellsPath,
    string HostSettingsPath,
    string Digest,
    ApplicationBundleManifest Manifest);
