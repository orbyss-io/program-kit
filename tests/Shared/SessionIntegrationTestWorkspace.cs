using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;

namespace Orbyss.ProgramKit.Tests;

internal sealed class SessionIntegrationTestWorkspace : IDisposable
{
    private readonly string root;

    private SessionIntegrationTestWorkspace(string root)
    {
        this.root = root;
    }

    public string Root => root;
    public string Feed => Path.Combine(root, ".feed");

    public static SessionIntegrationTestWorkspace Create()
    {
        string root = TestRepository.CreateEmptyWorkspace();
        Directory.CreateDirectory(Path.Combine(root, ".feed"));
        return new SessionIntegrationTestWorkspace(root);
    }

    public string PathOf(string logicalPath) => Path.Combine(root, logicalPath.Replace('/', Path.DirectorySeparatorChar));

    public void Write(string logicalPath, byte[] bytes)
    {
        string path = PathOf(logicalPath);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllBytes(path, bytes);
    }

    public string Fingerprint(string logicalPath) => $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(PathOf(logicalPath)))).ToLowerInvariant()}";

    public IReadOnlyDictionary<string, byte[]> Snapshot() => Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
        .ToDictionary(path => Path.GetRelativePath(root, path).Replace('\\', '/'), File.ReadAllBytes, StringComparer.Ordinal);

    public static ProcessStartInfo DeniedNetworkProcess(string executable, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = Path.GetTempPath(), RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        start.Environment["NUGET_PACKAGES"] = Path.Combine(Path.GetTempPath(), "program-kit-denied-network-packages");
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["http_proxy"] = "http://127.0.0.1:1";
        start.Environment["https_proxy"] = "http://127.0.0.1:1";
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        return start;
    }

    public void Dispose() => TestRepository.DeleteWorkspace(root);
}
