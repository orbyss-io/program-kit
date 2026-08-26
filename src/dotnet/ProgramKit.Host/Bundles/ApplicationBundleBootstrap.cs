using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

namespace ProgramKit.Host.Bundles;

internal static class ApplicationBundleBootstrap
{
    private const int SupportedSchemaVersion = 1;
    private const int SupportedHostApi = 1;
    private const int MaximumEntryCount = 4096;
    private const long MaximumExpandedBytes = 2L * 1024 * 1024 * 1024;

    public static ApplicationBundle Prepare(string[] args)
    {
        var path = ReadArgument(args, "--program-kit-bundle")
            ?? Environment.GetEnvironmentVariable("PROGRAMKIT_BUNDLE_PATH");

        if (string.IsNullOrWhiteSpace(path))
            return CreateDevelopmentBundle();

        var bundlePath = Path.GetFullPath(path);
        if (!File.Exists(bundlePath))
            throw new FileNotFoundException("The configured Program Kit application bundle does not exist.", bundlePath);

        var digest = ComputeSha256(bundlePath);
        var cacheRoot = Environment.GetEnvironmentVariable("PROGRAMKIT_BUNDLE_CACHE")
            ?? Path.Combine(AppContext.BaseDirectory, ".program-kit", "bundles");
        var destination = Path.Combine(Path.GetFullPath(cacheRoot), digest);

        if (!Directory.Exists(destination))
            ExtractAndVerify(bundlePath, destination);

        var manifest = LoadManifest(Path.Combine(destination, "manifest.json"));
        ValidateManifest(manifest, destination);
        return CreateBundle(destination, digest, manifest);
    }

    private static ApplicationBundle CreateDevelopmentBundle()
    {
        var root = AppContext.BaseDirectory;
        var manifest = new ApplicationBundleManifest
        {
            SchemaVersion = SupportedSchemaVersion,
            HostApi = SupportedHostApi,
            BundleId = "development",
            Version = "0.0.0-local",
            Files = [],
            Packages = []
        };
        return CreateBundle(root, "development", manifest);
    }

    private static ApplicationBundle CreateBundle(
        string root,
        string digest,
        ApplicationBundleManifest manifest) =>
        new(
            root,
            Path.Combine(root, "packages"),
            Path.Combine(root, "shells.json"),
            Path.Combine(root, "hostsettings.json"),
            digest,
            manifest);

    private static void ExtractAndVerify(string bundlePath, string destination)
    {
        var parent = Directory.GetParent(destination)?.FullName
            ?? throw new InvalidOperationException("Bundle extraction directory has no parent.");
        Directory.CreateDirectory(parent);
        var temporary = destination + ".tmp-" + Guid.NewGuid().ToString("N");
        Directory.CreateDirectory(temporary);

        try
        {
            using var archive = ZipFile.OpenRead(bundlePath);
            if (archive.Entries.Count > MaximumEntryCount)
                throw new InvalidDataException($"Bundle contains more than {MaximumEntryCount} entries.");

            var expandedBytes = archive.Entries.Sum(entry => entry.Length);
            if (expandedBytes > MaximumExpandedBytes)
                throw new InvalidDataException($"Bundle expands beyond {MaximumExpandedBytes} bytes.");

            foreach (var entry in archive.Entries)
            {
                if (IsSymbolicLink(entry))
                    throw new InvalidDataException($"Bundle entry '{entry.FullName}' is a symbolic link.");

                var target = ResolveEntryPath(temporary, entry.FullName);
                if (string.IsNullOrEmpty(entry.Name))
                {
                    Directory.CreateDirectory(target);
                    continue;
                }

                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                entry.ExtractToFile(target, overwrite: false);
            }

            var manifest = LoadManifest(Path.Combine(temporary, "manifest.json"));
            ValidateManifest(manifest, temporary);
            Directory.Move(temporary, destination);
        }
        catch
        {
            if (Directory.Exists(temporary))
                Directory.Delete(temporary, recursive: true);
            throw;
        }
    }

    private static ApplicationBundleManifest LoadManifest(string path)
    {
        if (!File.Exists(path))
            throw new InvalidDataException("Application bundle does not contain manifest.json.");

        var manifest = JsonSerializer.Deserialize<ApplicationBundleManifest>(
            File.ReadAllText(path),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        return manifest ?? throw new InvalidDataException("Application bundle manifest is invalid.");
    }

    private static void ValidateManifest(ApplicationBundleManifest manifest, string root)
    {
        if (manifest.SchemaVersion != SupportedSchemaVersion)
            throw new InvalidDataException($"Unsupported application bundle schema {manifest.SchemaVersion}.");
        if (manifest.HostApi != SupportedHostApi)
            throw new InvalidDataException($"Application bundle requires unsupported host API {manifest.HostApi}.");
        if (string.IsNullOrWhiteSpace(manifest.BundleId) || string.IsNullOrWhiteSpace(manifest.Version))
            throw new InvalidDataException("Application bundle identity is incomplete.");

        var declaredFiles = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var file in manifest.Files)
        {
            var path = ResolveEntryPath(root, file.Path);
            if (!declaredFiles.TryAdd(path, file.Sha256))
                throw new InvalidDataException($"Bundle file '{file.Path}' is declared more than once.");
            if (!File.Exists(path))
                throw new InvalidDataException($"Declared bundle file '{file.Path}' is missing.");
            var actual = ComputeSha256(path);
            if (!actual.Equals(file.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"Digest mismatch for bundle file '{file.Path}'.");
        }

        if (!File.Exists(Path.Combine(root, "shells.json")))
            throw new InvalidDataException("Application bundle does not contain shells.json.");

        var packagesRoot = Path.GetFullPath(Path.Combine(root, "packages"));
        Directory.CreateDirectory(packagesRoot);
        var declaredPackages = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var package in manifest.Packages)
        {
            if (string.IsNullOrWhiteSpace(package.Id) || string.IsNullOrWhiteSpace(package.Version))
                throw new InvalidDataException("Application bundle package identity is incomplete.");
            var path = ResolveEntryPath(root, package.Path);
            if (!string.Equals(Path.GetDirectoryName(path), packagesRoot, StringComparison.OrdinalIgnoreCase)
                || !path.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"Package '{package.Path}' must be a direct .nupkg child of packages/.");
            if (!declaredPackages.Add(path))
                throw new InvalidDataException($"Bundle package '{package.Path}' is declared more than once.");
            if (!declaredFiles.TryGetValue(path, out var fileDigest)
                || !fileDigest.Equals(package.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"Package '{package.Path}' is not hash-bound by the files manifest.");
        }

        var actualPackages = Directory
            .EnumerateFiles(packagesRoot, "*.nupkg", SearchOption.TopDirectoryOnly)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        if (!actualPackages.SetEquals(declaredPackages))
            throw new InvalidDataException("Application bundle package files do not match the packages manifest.");
    }

    private static string ResolveEntryPath(string root, string relativePath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) || Path.IsPathRooted(relativePath))
            throw new InvalidDataException($"Invalid bundle path '{relativePath}'.");

        var normalizedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var target = Path.GetFullPath(Path.Combine(normalizedRoot, relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!target.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"Bundle path '{relativePath}' escapes the extraction directory.");
        return target;
    }

    private static bool IsSymbolicLink(ZipArchiveEntry entry) =>
        ((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000;

    private static string ComputeSha256(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexStringLower(SHA256.HashData(stream));
    }

    private static string? ReadArgument(IReadOnlyList<string> args, string name)
    {
        for (var index = 0; index < args.Count; index++)
        {
            var argument = args[index];
            if (argument.StartsWith(name + "=", StringComparison.Ordinal))
                return argument[(name.Length + 1)..];
            if (argument.Equals(name, StringComparison.Ordinal) && index + 1 < args.Count)
                return args[index + 1];
        }
        return null;
    }
}
