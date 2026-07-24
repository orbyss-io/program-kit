using System.Security.Cryptography;
using System.Reflection;
using System.Globalization;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.ConformanceTests.Tasks;

[TestClass]
public sealed class TasksRuntimeConformanceTests
{
    [TestMethod]
    public void TaskPackagesRemainCshellsFree()
    {
        var taskSources = ConformanceInputs.Files("Source", "*.cs")
            .Where(path => path.Replace('\\', '/').Contains(
                "/Orbyss.ProgramKit.Tasks",
                StringComparison.Ordinal));

        foreach (var source in taskSources)
        {
            Assert.DoesNotContain(
                "CShells",
                File.ReadAllText(source),
                source);
        }
    }

    [TestMethod]
    public void ProviderNeutralSchedulesDoNotAcquireCronOrRuntimeOwnership()
    {
        var project = ConformanceInputs.Files("Projects", "*.csproj")
            .Single(path => string.Equals(
                Path.GetFileNameWithoutExtension(path),
                "Orbyss.ProgramKit.Tasks.Schedules",
                StringComparison.Ordinal));
        var source = ConformanceInputs.Files("Source", "*.cs")
            .Where(path => path.Replace('\\', '/').Contains(
                "/Orbyss.ProgramKit.Tasks.Schedules/",
                StringComparison.Ordinal) &&
                !path.Replace('\\', '/').Contains(
                    "/Orbyss.ProgramKit.Tasks.Schedules.Cronos/",
                    StringComparison.Ordinal))
            .Select(File.ReadAllText);
        var combined = string.Join("\n", source);

        Assert.DoesNotContain("Cronos", File.ReadAllText(project));
        Assert.DoesNotContain("CronExpression", combined);
        Assert.DoesNotContain("Channel<", combined);
        Assert.DoesNotContain("BackgroundService", combined);
    }

    [TestMethod]
    public void HostingRegistersHealthWithoutMappingAnEndpoint()
    {
        var hostingSources = ConformanceInputs.Files("Source", "*.cs")
            .Where(path => path.Replace('\\', '/').Contains(
                "/Orbyss.ProgramKit.Tasks.Hosting/",
                StringComparison.Ordinal))
            .Select(File.ReadAllText);
        var combined = string.Join("\n", hostingSources);

        Assert.Contains("program-kit-tasks-runtime-started", combined);
        Assert.Contains("program-kit-tasks-accepting", combined);
        Assert.Contains("program-kit-tasks-queue", combined);
        Assert.Contains("program-kit-tasks-registry", combined);
        Assert.Contains("program-kit-tasks-schedules", combined);
        Assert.DoesNotContain("MapHealthChecks", combined);
        Assert.DoesNotContain("MapGet", combined);
    }

    [TestMethod]
    public void InProcessTelemetryUsesMetadataOnlyActivityAndMeterSignals()
    {
        var sources = ConformanceInputs.Files("Source", "*.cs")
            .Where(path => path.Replace('\\', '/').Contains(
                "/Orbyss.ProgramKit.Tasks.InProcess/Observability/",
                StringComparison.Ordinal))
            .Select(File.ReadAllText);
        var combined = string.Join("\n", sources);

        Assert.Contains("ActivitySource", combined);
        Assert.Contains("Meter", combined);
        Assert.Contains("programkit.task.accepted", combined);
        Assert.Contains("programkit.task.terminal", combined);
        Assert.DoesNotContain("Payload", combined);
        Assert.DoesNotContain("Secret", combined);
        Assert.DoesNotContain("Principal", combined);
    }

    [TestMethod]
    public void CronosProviderEvidenceBindsTheSelectedPackageAndAsset()
    {
        var evidencePath = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "src",
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos",
            "Evidence",
            "cronos-0.13.0.json");
        using var document = JsonDocument.Parse(
            File.ReadAllBytes(evidencePath));
        var root = document.RootElement;

        Assert.AreEqual("0.13.0", root.GetProperty("packageVersion").GetString());
        Assert.AreEqual("cronos/0.13", root.GetProperty("dialect").GetString());
        Assert.AreEqual(
            "lib/net6.0/Cronos.dll",
            root.GetProperty("selectedAsset").GetString());
        Assert.AreEqual(
            "dependency-free net6.0 asset selected by a net10.0 consumer; not net10-native",
            root.GetProperty("runtimeClaim").GetString());
    }

    [TestMethod]
    public void LocalCronosBytesMatchTheApprovedEvidence()
    {
        var packageRoot = Path.Combine(
            Environment.GetFolderPath(
                Environment.SpecialFolder.UserProfile),
            ".nuget",
            "packages",
            "cronos",
            "0.13.0");
        var package = Path.Combine(packageRoot, "cronos.0.13.0.nupkg");
        var assembly = Path.Combine(packageRoot, "lib", "net6.0", "Cronos.dll");

        Assert.AreEqual(
            "6612c6605dc3d16f613052da3c5b22ba9e80c08253ccc5c91bb40b4c3a0939f7",
            Hash(package));
        Assert.AreEqual(
            "e0ad7c799904f1b663ab090b32665e0e90ede27699937588900845383064ba03",
            Hash(assembly));
        Assert.IsFalse(
            File.Exists(
                Path.Combine(
                    packageRoot,
                    "lib",
                    "net10.0",
                    "Cronos.dll")));
    }

    [TestMethod]
    public void CronosSelectedGrammarAndOccurrenceBoundariesMatchGoldenValues()
    {
        var assembly = LoadCronos();
        var standard = Format(assembly, "Standard");
        foreach (var expression in new[]
                 {
                     "*/5 0-23/2 * JAN,MAR MON-FRI",
                     "0 0 L * *",
                     "0 0 LW * *",
                     "0 0 15W * *",
                     "0 0 * * MON#2",
                     "@daily",
                 })
        {
            Assert.IsNotNull(Parse(assembly, expression, standard));
        }

        var seeded = Parse(assembly, "H H * * *", standard, 123);
        Assert.AreEqual("59 21 * * *", seeded.ToString());
        var includeSeconds = Format(assembly, "IncludeSeconds");
        var seconds = Parse(
            assembly,
            "*/15 * * * * *",
            includeSeconds);
        Assert.AreEqual(
            Instant("2025-01-01T00:00:15Z"),
            Next(
                assembly,
                seconds,
                Instant("2025-01-01T00:00:00Z"),
                TimeZoneInfo.Utc));
        var andExpression = Parse(
            assembly,
            "0 0 1 * MON",
            standard);
        Assert.AreEqual(
            Instant("2025-09-01T00:00:00Z"),
            Next(
                assembly,
                andExpression,
                Instant("2025-01-01T00:00:00Z"),
                TimeZoneInfo.Utc));
        Assert.AreEqual(
            Instant("2025-09-01T00:00:00Z"),
            Previous(
                assembly,
                andExpression,
                Instant("2025-09-02T00:00:00Z"),
                TimeZoneInfo.Utc));
    }

    [TestMethod]
    public void CronosIanaAndWindowsDstRulesMatchIndependentGoldenTimeline()
    {
        var assembly = LoadCronos();
        var expression = Parse(
            assembly,
            "30 2 * * *",
            Format(assembly, "Standard"));
        foreach (var zoneId in new[]
                 {
                     "Europe/Amsterdam",
                     "W. Europe Standard Time",
                 })
        {
            var zone = TimeZoneInfo.FindSystemTimeZoneById(zoneId);
            var spring = Next(
                assembly,
                expression,
                Instant("2025-03-29T02:00:00Z"),
                zone);
            var fall = Next(
                assembly,
                expression,
                Instant("2025-10-25T23:00:00Z"),
                zone);
            var afterFall = Next(assembly, expression, fall, zone);

            Assert.AreEqual(
                Instant("2025-03-30T01:00:00Z"),
                spring.ToUniversalTime());
            Assert.AreEqual(
                Instant("2025-10-26T00:30:00Z"),
                fall.ToUniversalTime());
            Assert.AreEqual(
                Instant("2025-10-27T01:30:00Z"),
                afterFall.ToUniversalTime());
        }
    }

    [TestMethod]
    public void CronosSelectionFingerprintRejectsChangedZoneEvidence()
    {
        var provider = Assembly.LoadFrom(
            Path.Combine(
                ConformanceInputs.RepositoryRoot,
                "program-kit",
                "src",
                "Orbyss.ProgramKit.Tasks.Schedules.Cronos",
                "bin",
                "Release",
                "net10.0",
                "Orbyss.ProgramKit.Tasks.Schedules.Cronos.dll"));
        var factoryType = provider.GetType(
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos.Factories.CronosScheduleDescriptorFactory",
            throwOnError: true)!;
        var factory = Activator.CreateInstance(factoryType)!;
        var formatType = provider.GetType(
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors.CronosScheduleFormat",
            throwOnError: true)!;
        var standard = Enum.Parse(formatType, "Standard");
        var horizonStart = Instant("2025-01-01T00:00:00Z");
        var horizonEnd = Instant("2026-01-01T00:00:00Z");
        var profile = new ArtifactReference(
            ProgramKitIdentifier.Parse(
                "pkid:profile:program-kit:test-cronos"),
            SemanticVersion.Parse("1.0.0"),
            Sha256Digest.Parse($"sha256:{new string('a', 64)}"));
        var create = factoryType.GetMethod("Create")!;
        var descriptor = create.Invoke(
            factory,
            [
                "0 0 * * *",
                standard,
                null,
                "Europe/Amsterdam",
                profile,
                "test-tzdata",
                "2025a",
                horizonStart,
                horizonEnd,
            ])!;
        var descriptorType = descriptor.GetType();
        var evidenceType = provider.GetType(
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos.Evidence.CronosTimeZoneSelectionEvidence",
            throwOnError: true)!;
        var changedEvidence = Activator.CreateInstance(
            evidenceType,
            "test-tzdata",
            "2025a",
            horizonStart,
            horizonEnd,
            Sha256Digest.Parse($"sha256:{new string('b', 64)}"))!;
        var changedDescriptor = Activator.CreateInstance(
            descriptorType,
            descriptorType.GetProperty("Expression")!.GetValue(descriptor),
            standard,
            null,
            "Europe/Amsterdam",
            profile,
            changedEvidence)!;
        var guard = provider.GetType(
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos.Validation.CronosDescriptorGuard",
            throwOnError: true)!;
        var validate = guard.GetMethod(
            "Validate",
            BindingFlags.Static | BindingFlags.NonPublic)!;

        var exception = Assert.ThrowsExactly<TargetInvocationException>(
            () => validate.Invoke(null, [changedDescriptor]));

        Assert.IsInstanceOfType<InvalidOperationException>(
            exception.InnerException);
    }

    private static string Hash(string path) =>
        Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));

    private static DateTimeOffset Instant(string value) =>
        DateTimeOffset.Parse(value, CultureInfo.InvariantCulture);

    private static Assembly LoadCronos()
    {
        var path = Path.Combine(
            Environment.GetFolderPath(
                Environment.SpecialFolder.UserProfile),
            ".nuget",
            "packages",
            "cronos",
            "0.13.0",
            "lib",
            "net6.0",
            "Cronos.dll");
        return Assembly.LoadFrom(path);
    }

    private static object Format(Assembly assembly, string name)
    {
        var type = assembly.GetType("Cronos.CronFormat", throwOnError: true)!;
        return Enum.Parse(type, name);
    }

    private static object Parse(
        Assembly assembly,
        string expression,
        object format,
        int? seed = null)
    {
        var expressionType = assembly.GetType(
            "Cronos.CronExpression",
            throwOnError: true)!;
        var formatType = format.GetType();
        var parameterTypes = seed is null
            ? new[] { typeof(string), formatType }
            : new[] { typeof(string), formatType, typeof(int) };
        var method = expressionType.GetMethod(
            "Parse",
            BindingFlags.Public | BindingFlags.Static,
            parameterTypes)!;
        var arguments = seed is null
            ? new[] { expression, format }
            : new object[] { expression, format, seed.Value };
        return method.Invoke(null, arguments)!;
    }

    private static DateTimeOffset Next(
        Assembly assembly,
        object expression,
        DateTimeOffset from,
        TimeZoneInfo zone) =>
        Occurrence(
            assembly,
            expression,
            "GetNextOccurrence",
            from,
            zone);

    private static DateTimeOffset Previous(
        Assembly assembly,
        object expression,
        DateTimeOffset from,
        TimeZoneInfo zone) =>
        Occurrence(
            assembly,
            expression,
            "GetPreviousOccurrence",
            from,
            zone);

    private static DateTimeOffset Occurrence(
        Assembly assembly,
        object expression,
        string methodName,
        DateTimeOffset from,
        TimeZoneInfo zone)
    {
        var expressionType = assembly.GetType(
            "Cronos.CronExpression",
            throwOnError: true)!;
        var method = expressionType.GetMethod(
            methodName,
            BindingFlags.Public | BindingFlags.Instance,
            [
                typeof(DateTimeOffset),
                typeof(TimeZoneInfo),
                typeof(bool),
            ])!;
        return (DateTimeOffset)method.Invoke(
            expression,
            [from, zone, false])!;
    }
}
