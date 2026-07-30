using System.Diagnostics;
using System.Text;

namespace Orbyss.ProgramKit.ConformanceTests.Infrastructure;

/// <summary>
/// Materializes exact external package archives into the NuGet global package
/// folder so evidence-binding tests can read the bytes they verify. Tests must
/// never assume ambient machine state: a fresh machine downloads the pinned
/// archive from nuget.org first, and every caller still verifies the recorded
/// digest of the downloaded bytes, so acquisition stays fail-closed.
/// </summary>
internal static class ExternalPackageArchives
{
    private static readonly Lock Gate = new();

    public static string EnsureDownloaded(string packageId, string version)
    {
        var packageRoot = Environment.GetEnvironmentVariable("NUGET_PACKAGES");
        if (string.IsNullOrWhiteSpace(packageRoot))
        {
            packageRoot = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                ".nuget",
                "packages");
        }

        var archive = Path.Combine(
            packageRoot,
            packageId.ToLowerInvariant(),
            version,
            string.Concat(packageId.ToLowerInvariant(), ".", version, ".nupkg"));
        lock (Gate)
        {
            if (!File.Exists(archive))
            {
                Download(packageId, version);
            }
        }

        if (!File.Exists(archive))
        {
            throw new FileNotFoundException(
                "Restore did not materialize the expected package archive.",
                archive);
        }

        return archive;
    }

    private static void Download(string packageId, string version)
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-package-download-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            File.WriteAllText(
                Path.Combine(root, "nuget.config"),
                """
                <?xml version="1.0" encoding="utf-8"?>
                <configuration>
                  <packageSources>
                    <clear />
                    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
                  </packageSources>
                </configuration>
                """,
                Encoding.UTF8);
            File.WriteAllText(
                Path.Combine(root, "Download.csproj"),
                $"""
                <Project Sdk="Microsoft.NET.Sdk">
                  <PropertyGroup>
                    <TargetFramework>net10.0</TargetFramework>
                  </PropertyGroup>
                  <ItemGroup>
                    <PackageDownload Include="{packageId}" Version="[{version}]" />
                  </ItemGroup>
                </Project>
                """,
                Encoding.UTF8);

            ProcessStartInfo startInfo = new("dotnet")
            {
                WorkingDirectory = root,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            startInfo.ArgumentList.Add("restore");
            startInfo.ArgumentList.Add("Download.csproj");
            using var process = Process.Start(startInfo)
                ?? throw new InvalidOperationException("Unable to start dotnet.");
            var output = process.StandardOutput.ReadToEndAsync();
            var error = process.StandardError.ReadToEndAsync();
            process.WaitForExit();
            Task.WaitAll(output, error);
            if (process.ExitCode != 0)
            {
                throw new InvalidOperationException(string.Concat(
                    "Downloading ",
                    packageId,
                    " ",
                    version,
                    " failed: ",
                    output.Result,
                    Environment.NewLine,
                    error.Result));
            }
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
