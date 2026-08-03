using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

internal static class TestRepository
{
    public static string Root { get; } = FindRoot();

    public static string CliExecutable
    {
        get
        {
            DirectoryInfo testOutput = new(AppContext.BaseDirectory);
            string configuration = testOutput.Parent?.Name ?? throw new InvalidOperationException("Test build configuration not found.");
            string targetFramework = testOutput.Name;
            return Path.Combine(Root, "src", "ProgramKit.Cli", "bin", configuration, targetFramework, OperatingSystem.IsWindows() ? "program-kit.exe" : "program-kit");
        }
    }

    public static string AdapterAssembly
    {
        get
        {
            DirectoryInfo testOutput = new(AppContext.BaseDirectory);
            string configuration = testOutput.Parent?.Name ?? throw new InvalidOperationException("Test build configuration not found.");
            string targetFramework = testOutput.Name;
            return Path.Combine(Root, "src", "ProgramKit.SpecKitAdapter", "bin", configuration, targetFramework, "program-kit-spec-kit-adapter.dll");
        }
    }

    public static string Fixture(string relative) => Path.Combine(Root, "tests", "Fixtures", "Reference.Status", relative.Replace('/', Path.DirectorySeparatorChar));

    public static string CreateWorkspace(bool includeMirror = false)
    {
        string root = Path.Combine(Path.GetTempPath(), "program-kit-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        CopyDirectory(Fixture("Valid/authority"), Path.Combine(root, "authority"));
        CopyDirectory(Fixture("Valid/definitions"), Path.Combine(root, "definitions"));
        CopyDirectory(Fixture("Valid/implementation"), Path.Combine(root, "implementation"));
        CopyDirectory(Fixture("Valid/requests"), Path.Combine(root, "requests"));
        if (includeMirror)
        {
            string mirror = Path.Combine(Root, "artifacts", "dependency-mirror");
            Assert.IsTrue(Directory.Exists(mirror), "Run eng/Bootstrap-DependencyMirror.ps1 before acceptance tests.");
            CopyDirectory(mirror, Path.Combine(root, "dependencies"));
        }

        return root;
    }

    public static string CreateEmptyWorkspace()
    {
        string root = Path.Combine(Path.GetTempPath(), "program-kit-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        return root;
    }

    public static string DigestTree(string root) => string.Join('\n', Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
        .OrderBy(path => Path.GetRelativePath(root, path), StringComparer.Ordinal)
        .Select(path => $"{Path.GetRelativePath(root, path).Replace('\\', '/')}:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)))}"));

    public static (int ExitCode, string StandardOutput, string StandardError) RunCli(params string[] arguments) =>
        RunCliWithEnvironment(new Dictionary<string, string>(StringComparer.Ordinal), arguments);

    public static (int ExitCode, string StandardOutput, string StandardError) RunAdapter(params string[] arguments)
    {
        ProcessStartInfo start = new("dotnet") { RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        start.ArgumentList.Add(AdapterAssembly);
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start the Program Kit Spec Kit adapter.");
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, stdout, stderr);
    }

    public static (int ExitCode, string StandardOutput, string StandardError) RunCliWithEnvironment(
        IReadOnlyDictionary<string, string> environment,
        params string[] arguments)
    {
        ProcessStartInfo start = new(CliExecutable) { RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach ((string key, string value) in environment)
        {
            start.Environment[key] = value;
        }

        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start Program Kit CLI.");
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, stdout, stderr);
    }

    public static void DeleteWorkspace(string root)
    {
        string temp = Path.GetFullPath(Path.Combine(Path.GetTempPath(), "program-kit-tests")).TrimEnd(Path.DirectorySeparatorChar);
        string target = Path.GetFullPath(root);
        if (!target.StartsWith(temp + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Unsafe test cleanup target.");
        if (Directory.Exists(target)) Directory.Delete(target, true);
    }

    private static string FindRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null && !File.Exists(Path.Combine(current.FullName, "global.json"))) current = current.Parent;
        return current?.FullName ?? throw new InvalidOperationException("Repository root not found.");
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (string directory in Directory.EnumerateDirectories(source)) CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }
}
