using System.Diagnostics;

namespace Orbyss.ProgramKit.ConformanceTests.Targeting;

[TestClass]
public sealed class TargetProfileEnforcementTests
{
    private static readonly (string Property, string Value, string Diagnostic)[] InvalidOverrides =
    [
        ("TargetFrameworks", "net10.0%3Bnet9.0", "PKNET001"),
        ("TargetFramework", "net9.0", "PKNET002"),
        ("LangVersion", "latest", "PKNET003"),
        ("NETCoreSdkVersion", "10.0.301", "PKNET004"),
        (
            "ProgramKitTargetProfileId",
            "pkid:profile:program-kit:another-profile",
            "PKNET005"),
        ("ProgramKitTargetProfileVersion", "2.0.0", "PKNET006"),
        ("ProgramKitSdkRollForward", "latestPatch", "PKNET007"),
        ("ProgramKitAllowPrereleaseSdk", "true", "PKNET008"),
    ];

    [TestMethod]
    public async Task EveryCanonicalTargetProfileOverrideFailsWithItsStableDiagnostic()
    {
        var probe = Path.Combine(
            AppContext.BaseDirectory,
            "ConformanceInputs",
            "TargetProfileProbe.csproj");
        Assert.IsTrue(File.Exists(probe), probe);

        var accepted = await RunValidationAsync(probe, null, null);
        Assert.AreEqual(0, accepted.ExitCode, accepted.Output);

        foreach (var (property, value, diagnostic) in InvalidOverrides)
        {
            var rejected = await RunValidationAsync(probe, property, value);
            Assert.AreNotEqual(0, rejected.ExitCode, $"{property} unexpectedly passed.");
            Assert.Contains(
                diagnostic,
                rejected.Output,
                StringComparison.Ordinal);
        }
    }

    private static async Task<ValidationProcessResult> RunValidationAsync(
        string probe,
        string? property,
        string? value)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            WorkingDirectory = Path.GetDirectoryName(probe)!,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        startInfo.ArgumentList.Add("msbuild");
        startInfo.ArgumentList.Add(probe);
        startInfo.ArgumentList.Add("--target:ValidateProgramKitTargetProfile");
        startInfo.ArgumentList.Add("--nologo");
        startInfo.ArgumentList.Add("--verbosity:quiet");
        if (property is not null)
        {
            startInfo.ArgumentList.Add($"--property:{property}={value}");
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start the .NET SDK process.");
        var standardOutput = process.StandardOutput.ReadToEndAsync();
        var standardError = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        return new ValidationProcessResult(
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }

}
