using System.Collections.Immutable;
using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Security;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Playwright;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Generation.Keycloak;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

[TestClass]
[DoNotParallelize]
public sealed class KeycloakLocalFixtureConformanceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task GeneratedAppHostRestoresAndBuildsWithoutStartingResources()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-keycloak-build-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var appHost = await WriteGeneratedFixtureAsync(root);
            await File.WriteAllTextAsync(
                Path.Combine(appHost, "NuGet.Config"),
                NuGetConfiguration,
                TestContext.CancellationToken);

            var restore = await RunDotNetAsync(
                appHost,
                TestContext.CancellationToken,
                "restore",
                "AppHost.csproj",
                "--configfile",
                "NuGet.Config",
                "--force-evaluate",
                "-p:NuGetAudit=false",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            var build = await RunDotNetAsync(
                appHost,
                TestContext.CancellationToken,
                "build",
                "AppHost.csproj",
                "--no-restore",
                "--configuration",
                "Release",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, build.ExitCode, build.Output);

            var assets = await File.ReadAllTextAsync(
                Path.Combine(appHost, "obj", "project.assets.json"),
                TestContext.CancellationToken);
            var packageLock = await File.ReadAllTextAsync(
                Path.Combine(appHost, "packages.lock.json"),
                TestContext.CancellationToken);
            Assert.Contains(
                "Aspire.Hosting.Keycloak/13.4.6-preview.1.26319.6",
                assets);
            Assert.Contains(
                "\"resolved\": \"13.4.6-preview.1.26319.6\"",
                packageLock);
            Assert.DoesNotContain("Orbyss.ProgramKit", assets);
            Assert.IsFalse(Directory.Exists(Path.Combine(appHost, ".aspire")));
            Assert.IsFalse(Directory.Exists(Path.Combine(appHost, "logs")));
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, true);
            }
        }
    }

    [TestMethod]
    public async Task GeneratedSecurityConsumersRestoreBuildAndHaveNoKitRuntimeDependency()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-keycloak-consumers-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            _ = await WriteGeneratedFixtureAsync(root);
            var projects = new[]
            {
                "SecurityHost/SecurityHost.csproj",
                "PublicBrowser/PublicBrowser.csproj",
                "PublicBrowserVerification/PublicBrowserVerification.csproj",
            };
            foreach (var project in projects)
            {
                var projectPath = Path.Combine(
                    root,
                    "KeycloakFixture",
                    "GeneratedConsumers",
                    project.Replace('/', Path.DirectorySeparatorChar));
                var projectRoot = Path.GetDirectoryName(projectPath)!;
                var nuget = Path.Combine(projectRoot, "NuGet.Config");
                await File.WriteAllTextAsync(
                    nuget,
                    NuGetConfiguration,
                    TestContext.CancellationToken);
                var restore = await RunDotNetAsync(
                    projectRoot,
                    TestContext.CancellationToken,
                    "restore",
                    Path.GetFileName(projectPath),
                    "--configfile",
                    "NuGet.Config",
                    "--force-evaluate",
                    "-p:NuGetAudit=false",
                    "--verbosity",
                    "minimal");
                Assert.AreEqual(0, restore.ExitCode, restore.Output);
                var build = await RunDotNetAsync(
                    projectRoot,
                    TestContext.CancellationToken,
                    "build",
                    Path.GetFileName(projectPath),
                    "--no-restore",
                    "--configuration",
                    "Release",
                    "--verbosity",
                    "minimal");
                Assert.AreEqual(0, build.ExitCode, build.Output);
                var assets = await File.ReadAllTextAsync(
                    Path.Combine(projectRoot, "obj", "project.assets.json"),
                    TestContext.CancellationToken);
                Assert.DoesNotContain("Orbyss.ProgramKit", assets);
            }
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, true);
            }
        }
    }

    [TestMethod]
    public async Task GeneratedTlsSourcesCreateExactTrustAndCleanOwnedState()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-keycloak-crypto-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            KeycloakLocalFixtureGenerator generator = new();
            var generated = generator.Generate(Definition());
            foreach (var relativePath in new[]
                     {
                         "KeycloakFixture/AppHost/ProgramKitFixtureTls.cs",
                         "KeycloakFixture/AppHost/ProgramKitFixtureTrust.cs",
                         "KeycloakFixture/AppHost/global.json",
                     })
            {
                var output = generated.Outputs.Single(candidate =>
                    candidate.RelativePath == relativePath);
                await File.WriteAllBytesAsync(
                    Path.Combine(root, Path.GetFileName(relativePath)),
                    output.Content.ToArray(),
                    TestContext.CancellationToken);
            }

            await File.WriteAllTextAsync(
                Path.Combine(root, "Probe.csproj"),
                TlsProbeProject,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                Path.Combine(root, "Program.cs"),
                TlsProbeProgram,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                Path.Combine(root, "NuGet.Config"),
                NuGetConfiguration,
                TestContext.CancellationToken);

            var restore = await RunDotNetAsync(
                root,
                TestContext.CancellationToken,
                "restore",
                "Probe.csproj",
                "--configfile",
                "NuGet.Config",
                "--force-evaluate",
                "-p:NuGetAudit=false",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            var run = await RunDotNetAsync(
                root,
                TestContext.CancellationToken,
                "run",
                "--project",
                "Probe.csproj",
                "--no-restore",
                "--configuration",
                "Release",
                "--",
                root);
            Assert.AreEqual(0, run.ExitCode, run.Output);
            Assert.IsFalse(Directory.Exists(Path.Combine(root, "tls")));
        }
        finally
        {
            if (Directory.Exists(root))
            {
                await DeleteDirectoryWithRetryAsync(
                    root,
                    CancellationToken.None);
            }
        }
    }

    [TestMethod]
    public async Task ExactPackageAndSelectionEvidenceMatchReviewedBytes()
    {
        var packagePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            ".nuget",
            "packages",
            "aspire.hosting.keycloak",
            KeycloakLocalFixtureCatalog.AspireKeycloakPackageVersion,
            string.Concat(
                "aspire.hosting.keycloak.",
                KeycloakLocalFixtureCatalog.AspireKeycloakPackageVersion,
                ".nupkg"));
        Assert.IsTrue(
            File.Exists(packagePath),
            "Run the generated AppHost restore before package-byte conformance.");
        var packageDigest = Convert.ToHexStringLower(
            SHA256.HashData(
                await File.ReadAllBytesAsync(
                    packagePath,
                    TestContext.CancellationToken)));
        Assert.AreEqual(
            KeycloakLocalFixtureCatalog.AspireKeycloakPackageSha256,
            packageDigest);

        var evidencePath = FindProgramKitPath(
            "src",
            "Orbyss.ProgramKit.DotNet",
            "Evidence",
            "dotnet-keycloak-local-fixture-selection-1.0.0.json");
        using var evidence = JsonDocument.Parse(
            await File.ReadAllTextAsync(
                evidencePath,
                TestContext.CancellationToken));
        Assert.AreEqual(
            KeycloakLocalFixtureCatalog.KeycloakVersion,
            evidence.RootElement.GetProperty("selection")
                .GetProperty("keycloakVersion")
                .GetString());
        Assert.AreEqual(
            string.Concat(
                "sha256:",
                KeycloakLocalFixtureCatalog.KeycloakImageSha256),
            evidence.RootElement.GetProperty("containerImage")
                .GetProperty("digest")
                .GetString());
        Assert.AreEqual(
            "not-supported-by-provider",
            evidence.RootElement.GetProperty("protocolCapabilities")
                .GetProperty("rfc8693StandardTokenExchange")
                .GetProperty("resourceParameter")
                .GetString());
    }

    [TestMethod]
    public void GeneratedOutputsContainNoReferenceIdentityOrSecretValue()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var text = string.Join(
            Environment.NewLine,
            result.Outputs.Select(output =>
                Encoding.UTF8.GetString(output.Content.Span)));

        Assert.DoesNotContain("pkid:secret-reference:fixture:", text);
        Assert.DoesNotContain("fixture-secret-value", text);
        Assert.DoesNotContain("\"secret\": \"admin", text);
        Assert.Contains("${PROGRAM_KIT_CONFIDENTIAL_CLIENT_SECRET}", text);
        Assert.Contains("\"executionAuthorized\": false", text);
    }

    [TestMethod]
    [TestCategory("ContainerIntegration")]
    public async Task ExplicitLinuxProfileRunsGeneratedTopologyAndAdditiveVectors()
    {
        if (!string.Equals(
                Environment.GetEnvironmentVariable(
                    "PROGRAM_KIT_RUN_KEYCLOAK_FIXTURE"),
                "1",
                StringComparison.Ordinal))
        {
            Assert.Inconclusive(
                "Set PROGRAM_KIT_RUN_KEYCLOAK_FIXTURE=1 to run the human-started disposable profile.");
        }

        if (!OperatingSystem.IsLinux())
        {
            Assert.Inconclusive(
                "The full generated-profile acceptance lane requires the exact selected Linux environment.");
        }

        Assert.AreEqual(
            "sha256:f66fd68d1888b33b7b3419e124b0482ff73c9000832446c8338ac7b9d0e77e35",
            Environment.GetEnvironmentVariable(
                "PROGRAM_KIT_KEYCLOAK_LINUX_ENVIRONMENT"),
            "The exact reviewed Linux environment selection was not bound.");

        var fixtureBase = ResolveFixtureBase();
        var root = Path.Combine(
            fixtureBase,
            string.Concat(
                "program-kit-keycloak-",
                Guid.NewGuid().ToString("N")[..8]));
        Directory.CreateDirectory(root);
        Process? appHost = null;
        Process? securityHost = null;
        Process? publicBrowser = null;
        Task<string>? standardOutput = null;
        Task<string>? standardError = null;
        Task<string>? securityHostOutput = null;
        Task<string>? securityHostError = null;
        Task<string>? publicBrowserOutput = null;
        Task<string>? publicBrowserError = null;
        var secrets = CreateRuntimeSecrets();
        var baselineContainers = await GetKeycloakContainerIdsAsync(
            TestContext.CancellationToken);
        try
        {
            var appHostDirectory = await WriteGeneratedFixtureAsync(root);
            await File.WriteAllTextAsync(
                Path.Combine(appHostDirectory, "NuGet.Config"),
                NuGetConfiguration,
                TestContext.CancellationToken);
            var restore = await RunDotNetAsync(
                appHostDirectory,
                TestContext.CancellationToken,
                "restore",
                "AppHost.csproj",
                "--configfile",
                "NuGet.Config",
                "--force-evaluate",
                "-p:NuGetAudit=false",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, restore.ExitCode, Sanitize(restore.Output, secrets));
            var build = await RunDotNetAsync(
                appHostDirectory,
                TestContext.CancellationToken,
                "build",
                "AppHost.csproj",
                "--no-restore",
                "--configuration",
                "Release",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, build.ExitCode, Sanitize(build.Output, secrets));
            await RestoreAndBuildGeneratedConsumersAsync(
                root,
                secrets,
                TestContext.CancellationToken);

            var startInfo = AppHostStartInfo(
                appHostDirectory,
                root,
                secrets);
            appHost = Process.Start(startInfo) ??
                throw new InvalidOperationException(
                    "The disposable Aspire AppHost did not start.");
            standardOutput = appHost.StandardOutput.ReadToEndAsync(
                TestContext.CancellationToken);
            standardError = appHost.StandardError.ReadToEndAsync(
                TestContext.CancellationToken);

            var trust = await WaitForExactTrustAsync(
                root,
                appHost,
                standardOutput,
                standardError,
                secrets,
                TestContext.CancellationToken);
            using var handler = CreateExactTrustHandler(
                trust.AuthorityCertificatePath);
            using HttpClient client = new(handler)
            {
                Timeout = TimeSpan.FromSeconds(10),
            };
            var metadata = await WaitForMetadataAsync(
                client,
                appHost,
                standardOutput,
                standardError,
                secrets,
                TestContext.CancellationToken);
            Assert.AreEqual(
                Definition().Authority.AbsoluteUri.TrimEnd('/'),
                metadata.GetProperty("issuer").GetString());
            var jsonWebKeySet = await GetJsonWebKeySetAsync(
                client,
                metadata,
                TestContext.CancellationToken);

            var securityHostDirectory = Path.Combine(
                root,
                "KeycloakFixture",
                "GeneratedConsumers",
                "SecurityHost");
            securityHost = Process.Start(
                    GeneratedConsumerStartInfo(
                        securityHostDirectory,
                        "SecurityHost.csproj",
                        "https://localhost:8443",
                        root,
                        secrets)) ??
                throw new InvalidOperationException(
                    "The generated security host did not start.");
            securityHostOutput = securityHost.StandardOutput.ReadToEndAsync(
                TestContext.CancellationToken);
            securityHostError = securityHost.StandardError.ReadToEndAsync(
                TestContext.CancellationToken);
            await WaitForGeneratedConsumerAsync(
                client,
                new Uri("https://localhost:8443/"),
                securityHost,
                securityHostOutput,
                securityHostError,
                secrets,
                TestContext.CancellationToken);
            using (var denied = await client.GetAsync(
                       "https://localhost:8443/protected",
                       TestContext.CancellationToken))
            {
                Assert.AreEqual(HttpStatusCode.Unauthorized, denied.StatusCode);
            }

            using (var service = await client.PostAsync(
                       "https://localhost:8443/oauth/client-credentials",
                       null,
                       TestContext.CancellationToken))
            {
                Assert.AreEqual(HttpStatusCode.OK, service.StatusCode);
            }

            using (var exchange = await client.PostAsync(
                       "https://localhost:8443/oauth/token-exchange",
                       null,
                       TestContext.CancellationToken))
            {
                Assert.AreEqual(HttpStatusCode.OK, exchange.StatusCode);
            }

            using (var roundTrip = await client.PostAsync(
                       "https://localhost:8443/oauth/protected-roundtrip",
                       null,
                       TestContext.CancellationToken))
            {
                Assert.AreEqual(HttpStatusCode.OK, roundTrip.StatusCode);
            }

            var initialKeyIds = JsonWebKeyIds(jsonWebKeySet);
            await RotateFixtureSigningKeyAsync(
                client,
                secrets,
                TestContext.CancellationToken);
            var rotatedKeys = await WaitForJsonWebKeyRolloverAsync(
                client,
                metadata,
                initialKeyIds,
                TestContext.CancellationToken);
            Assert.IsGreaterThan(0, rotatedKeys.Except(initialKeyIds).Count());
            using (var rollover = await client.PostAsync(
                       "https://localhost:8443/oauth/protected-roundtrip-after-rollover",
                       null,
                       TestContext.CancellationToken))
            {
                Assert.AreEqual(HttpStatusCode.OK, rollover.StatusCode);
            }

            var publicBrowserDirectory = Path.Combine(
                root,
                "KeycloakFixture",
                "GeneratedConsumers",
                "PublicBrowser");
            publicBrowser = Process.Start(
                    GeneratedConsumerStartInfo(
                        publicBrowserDirectory,
                        "PublicBrowser.csproj",
                        "https://localhost:7443",
                        root,
                        secrets)) ??
                throw new InvalidOperationException(
                    "The generated public browser host did not start.");
            publicBrowserOutput = publicBrowser.StandardOutput.ReadToEndAsync(
                TestContext.CancellationToken);
            publicBrowserError = publicBrowser.StandardError.ReadToEndAsync(
                TestContext.CancellationToken);
            await WaitForGeneratedConsumerAsync(
                client,
                Definition().PublicBrowserOrigin,
                publicBrowser,
                publicBrowserOutput,
                publicBrowserError,
                secrets,
                TestContext.CancellationToken);
            await RunGeneratedConfidentialFlowAsync(
                trust.ChromiumSpkiList,
                secrets,
                TestContext.CancellationToken);
            await RunGeneratedPublicBrowserFlowAsync(
                trust.ChromiumSpkiList,
                secrets,
                TestContext.CancellationToken);

            // Additive raw protocol vectors verify response-level properties
            // that are intentionally not disclosed by generated consumers.
            var serviceToken = await RequestClientCredentialsAsync(
                client,
                Definition().ServiceClientId,
                secrets.ServiceClientSecret,
                TestContext.CancellationToken);
            VerifyAccessToken(serviceToken, Definition(), jsonWebKeySet);
            var subjectToken = await RequestClientCredentialsAsync(
                client,
                Definition().TokenExchangeClientId,
                secrets.TokenExchangeClientSecret,
                TestContext.CancellationToken);
            var exchangedToken = await RequestTokenExchangeAsync(
                client,
                subjectToken,
                secrets.TokenExchangeClientSecret,
                TestContext.CancellationToken);
            VerifyAccessToken(exchangedToken, Definition(), jsonWebKeySet);
            Assert.AreNotEqual(subjectToken, exchangedToken);

            using var rejected = await RequestWrongSecretAsync(
                client,
                Definition().ServiceClientId,
                TestContext.CancellationToken);
            Assert.IsTrue(
                rejected.StatusCode is HttpStatusCode.BadRequest or
                    HttpStatusCode.Unauthorized);

            await RunBrowserCodeFlowAsync(
                client,
                metadata,
                jsonWebKeySet,
                Definition().PublicClientId,
                Definition().PublicRedirectUri,
                null,
                trust.ChromiumSpkiList,
                secrets,
                TestContext.CancellationToken);
            await RunBrowserCodeFlowAsync(
                client,
                metadata,
                jsonWebKeySet,
                Definition().ConfidentialClientId,
                Definition().ConfidentialRedirectUri,
                secrets.ConfidentialClientSecret,
                trust.ChromiumSpkiList,
                secrets,
                TestContext.CancellationToken);
        }
        finally
        {
            await StopProcessAsync(publicBrowser);
            await StopProcessAsync(securityHost);
            if (appHost is { HasExited: false })
            {
                appHost.Kill(true);
                await appHost.WaitForExitAsync(CancellationToken.None);
            }

            appHost?.Dispose();
            publicBrowser?.Dispose();
            securityHost?.Dispose();
            if (publicBrowserOutput is not null)
            {
                _ = Sanitize(await publicBrowserOutput, secrets);
            }

            if (publicBrowserError is not null)
            {
                _ = Sanitize(await publicBrowserError, secrets);
            }

            if (securityHostOutput is not null)
            {
                _ = Sanitize(await securityHostOutput, secrets);
            }

            if (securityHostError is not null)
            {
                _ = Sanitize(await securityHostError, secrets);
            }
            if (standardOutput is not null)
            {
                _ = Sanitize(await standardOutput, secrets);
            }

            if (standardError is not null)
            {
                _ = Sanitize(await standardError, secrets);
            }

            await WaitForOwnedContainersToStopAsync(
                baselineContainers,
                CancellationToken.None);
            if (Directory.Exists(root))
            {
                await DeleteDirectoryWithRetryAsync(
                    root,
                    CancellationToken.None);
            }
        }
    }

    internal static KeycloakLocalFixtureDefinition Definition() =>
        new(
            new ProgramKitIdentifier("pkid:fixture:program-kit:keycloak-local"),
            new SemanticVersion("1.0.0"),
            "program-kit",
            new Uri("https://localhost:5443/realms/program-kit"),
            new Uri(
                "https://localhost:5443/realms/program-kit/.well-known/openid-configuration"),
            "program-kit-api",
            "program-kit.api",
            "program-kit-public",
            new Uri("https://localhost:7443/authentication/login-callback"),
            new Uri("https://localhost:7443/authentication/logout-callback"),
            new Uri("https://localhost:7443/"),
            "program-kit-confidential",
            new Uri("https://localhost:8443/signin-oidc"),
            "program-kit-service",
            "program-kit-exchange",
            "fixture-principal",
            new KeycloakLocalFixtureSecretReferences(
                Secret("admin-password"),
                Secret("principal-password"),
                Secret("confidential-client-secret"),
                Secret("service-client-secret"),
                Secret("exchange-client-secret")));

    internal static async Task<string> WriteGeneratedFixtureAsync(string root)
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        foreach (var output in result.Outputs)
        {
            var path = Path.Combine(
                root,
                output.RelativePath.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            await File.WriteAllBytesAsync(
                path,
                output.Content.ToArray(),
                CancellationToken.None);
        }

        return Path.Combine(root, "KeycloakFixture", "AppHost");
    }

    internal static async Task<(int ExitCode, string Output)> RunDotNetAsync(
        string workingDirectory,
        CancellationToken cancellationToken,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                "The bounded dotnet process did not start.");
        var standardOutput = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var standardError = process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);
        return (
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }

    private static SecretReferenceDescriptor Secret(string name) =>
        new(
            new ProgramKitIdentifier(
                string.Concat("pkid:secret-reference:fixture:", name)),
            SecretReferenceClassification.RestrictedMetadata,
            SecretResultKind.ConfigurationText,
            Reference("pkid:capability:fixture:secret-resolver"),
            Reference(string.Concat("pkid:locator:fixture:", name)),
            SecretReferenceClassification.SensitiveMetadata);

    private static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                string.Concat("sha256:", new string('b', 64))));

    private static ProcessStartInfo AppHostStartInfo(
        string workingDirectory,
        string runtimeRoot,
        KeycloakFixtureRuntimeSecrets secrets)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        startInfo.ArgumentList.Add("run");
        startInfo.ArgumentList.Add("--project");
        startInfo.ArgumentList.Add("AppHost.csproj");
        startInfo.ArgumentList.Add("--no-build");
        startInfo.ArgumentList.Add("--no-restore");
        startInfo.ArgumentList.Add("--configuration");
        startInfo.ArgumentList.Add("Release");
        startInfo.Environment["DOTNET_ENVIRONMENT"] = "Development";
        startInfo.Environment["ASPNETCORE_ENVIRONMENT"] = "Development";
        startInfo.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        startInfo.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        startInfo.Environment["DOTNET_NOLOGO"] = "1";
        startInfo.Environment[
            KeycloakLocalFixtureCatalog.TlsProfile
                .RuntimeRootEnvironmentVariable] = runtimeRoot;
        startInfo.Environment["Parameters__keycloak-admin-username"] =
            "fixture-admin";
        startInfo.Environment["Parameters__keycloak-admin-password"] =
            secrets.AdminPassword;
        startInfo.Environment["Parameters__keycloak-test-principal-password"] =
            secrets.TestPrincipalPassword;
        startInfo.Environment["Parameters__keycloak-confidential-client-secret"] =
            secrets.ConfidentialClientSecret;
        startInfo.Environment["Parameters__keycloak-service-client-secret"] =
            secrets.ServiceClientSecret;
        startInfo.Environment["Parameters__keycloak-token-exchange-client-secret"] =
            secrets.TokenExchangeClientSecret;
        return startInfo;
    }

    private static async Task RestoreAndBuildGeneratedConsumersAsync(
        string runtimeRoot,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        var consumerRoot = Path.Combine(
            runtimeRoot,
            "KeycloakFixture",
            "GeneratedConsumers");
        foreach (var relativeProject in new[]
                 {
                     "SecurityHost/SecurityHost.csproj",
                     "PublicBrowser/PublicBrowser.csproj",
                     "PublicBrowserVerification/PublicBrowserVerification.csproj",
                 })
        {
            var project = Path.Combine(
                consumerRoot,
                relativeProject.Replace(
                    '/',
                    Path.DirectorySeparatorChar));
            var projectRoot = Path.GetDirectoryName(project)!;
            await File.WriteAllTextAsync(
                Path.Combine(projectRoot, "NuGet.Config"),
                NuGetConfiguration,
                cancellationToken);
            var restore = await RunDotNetAsync(
                projectRoot,
                cancellationToken,
                "restore",
                Path.GetFileName(project),
                "--configfile",
                "NuGet.Config",
                "--force-evaluate",
                "-p:NuGetAudit=false",
                "--verbosity",
                "minimal");
            Assert.AreEqual(
                0,
                restore.ExitCode,
                Sanitize(restore.Output, secrets));
            var build = await RunDotNetAsync(
                projectRoot,
                cancellationToken,
                "build",
                Path.GetFileName(project),
                "--no-restore",
                "--configuration",
                "Release",
                "--verbosity",
                "minimal");
            Assert.AreEqual(
                0,
                build.ExitCode,
                Sanitize(build.Output, secrets));
        }
    }

    private static ProcessStartInfo GeneratedConsumerStartInfo(
        string workingDirectory,
        string project,
        string address,
        string runtimeRoot,
        KeycloakFixtureRuntimeSecrets secrets)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        startInfo.ArgumentList.Add("run");
        startInfo.ArgumentList.Add("--project");
        startInfo.ArgumentList.Add(project);
        startInfo.ArgumentList.Add("--no-build");
        startInfo.ArgumentList.Add("--no-restore");
        startInfo.ArgumentList.Add("--configuration");
        startInfo.ArgumentList.Add("Release");
        startInfo.Environment["ASPNETCORE_URLS"] = address;
        startInfo.Environment["DOTNET_ENVIRONMENT"] = "Development";
        startInfo.Environment["ASPNETCORE_ENVIRONMENT"] = "Development";
        startInfo.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        startInfo.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        startInfo.Environment["DOTNET_NOLOGO"] = "1";
        startInfo.Environment[
            KeycloakLocalFixtureCatalog.TlsProfile
                .RuntimeRootEnvironmentVariable] = runtimeRoot;
        var tlsRoot = Path.Combine(runtimeRoot, "tls");
        startInfo.Environment[
            "ASPNETCORE_Kestrel__Certificates__Default__Path"] =
            Path.Combine(tlsRoot, "keycloak-server-certificate.pem");
        startInfo.Environment[
            "ASPNETCORE_Kestrel__Certificates__Default__KeyPath"] =
            Path.Combine(tlsRoot, "keycloak-server-private-key.pem");
        if (string.Equals(
                project,
                "SecurityHost.csproj",
                StringComparison.Ordinal))
        {
            startInfo.Environment["Authentication__Oidc__ClientSecret"] =
                secrets.ConfidentialClientSecret;
            startInfo.Environment["PROGRAM_KIT_SERVICE_CLIENT_SECRET"] =
                secrets.ServiceClientSecret;
            startInfo.Environment[
                "PROGRAM_KIT_TOKEN_EXCHANGE_CLIENT_SECRET"] =
                secrets.TokenExchangeClientSecret;
        }

        return startInfo;
    }

    private static async Task WaitForGeneratedConsumerAsync(
        HttpClient client,
        Uri address,
        Process process,
        Task<string> standardOutput,
        Task<string> standardError,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(45);
        while (DateTimeOffset.UtcNow < deadline)
        {
            if (process.HasExited)
            {
                throw new InvalidOperationException(
                    string.Concat(
                        "A generated consumer exited before readiness.",
                        Environment.NewLine,
                        Sanitize(await standardOutput, secrets),
                        Environment.NewLine,
                        Sanitize(await standardError, secrets)));
            }

            try
            {
                using var response = await client.GetAsync(
                    address,
                    cancellationToken);
                if (response.IsSuccessStatusCode)
                {
                    return;
                }
            }
            catch (HttpRequestException)
            {
            }
            catch (TaskCanceledException)
                when (!cancellationToken.IsCancellationRequested)
            {
            }

            await Task.Delay(
                TimeSpan.FromMilliseconds(250),
                cancellationToken);
        }

        throw new TimeoutException(
            "A generated consumer did not become ready within 45 seconds.");
    }

    private static async Task StopProcessAsync(Process? process)
    {
        if (process is { HasExited: false })
        {
            process.Kill(true);
            await process.WaitForExitAsync(CancellationToken.None);
        }
    }

    private static string ResolveFixtureBase()
    {
        var configured = Environment.GetEnvironmentVariable(
            "PROGRAM_KIT_KEYCLOAK_FIXTURE_BASE");
        var root = Path.GetFullPath(
            string.IsNullOrWhiteSpace(configured)
                ? Path.GetTempPath()
                : configured);
        var pathRoot = Path.GetPathRoot(root);
        if (string.Equals(
                root.TrimEnd(Path.DirectorySeparatorChar),
                pathRoot?.TrimEnd(Path.DirectorySeparatorChar),
                OperatingSystem.IsWindows()
                    ? StringComparison.OrdinalIgnoreCase
                    : StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "The Keycloak fixture base must not be a filesystem root.");
        }

        Directory.CreateDirectory(root);
        return root;
    }

    private static async Task<JsonElement> WaitForMetadataAsync(
        HttpClient client,
        Process appHost,
        Task<string> standardOutput,
        Task<string> standardError,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow.AddMinutes(3);
        while (DateTimeOffset.UtcNow < deadline)
        {
            if (appHost.HasExited)
            {
                throw new InvalidOperationException(
                    string.Concat(
                        "The disposable Aspire AppHost exited before Keycloak became ready.",
                        Environment.NewLine,
                        Sanitize(await standardOutput, secrets),
                        Environment.NewLine,
                        Sanitize(await standardError, secrets)));
            }

            try
            {
                using var response = await client.GetAsync(
                    Definition().MetadataAddress,
                    cancellationToken);
                if (response.IsSuccessStatusCode)
                {
                    using var document = JsonDocument.Parse(
                        await response.Content.ReadAsStreamAsync(
                            cancellationToken));
                    return document.RootElement.Clone();
                }
            }
            catch (HttpRequestException)
            {
            }
            catch (TaskCanceledException) when (!cancellationToken.IsCancellationRequested)
            {
            }

            await Task.Delay(TimeSpan.FromSeconds(1), cancellationToken);
        }

        if (!appHost.HasExited)
        {
            appHost.Kill(true);
            await appHost.WaitForExitAsync(CancellationToken.None);
        }

        throw new TimeoutException(
            string.Concat(
                "Keycloak did not expose its exact local metadata address within three minutes.",
                Environment.NewLine,
                Sanitize(await standardOutput, secrets),
                Environment.NewLine,
                Sanitize(await standardError, secrets)));
    }

    private static async Task<KeycloakFixtureTrust> WaitForExactTrustAsync(
        string runtimeRoot,
        Process appHost,
        Task<string> standardOutput,
        Task<string> standardError,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        var descriptorPath = Path.Combine(
            runtimeRoot,
            "tls",
            "trust.runtime.json");
        var deadline = DateTimeOffset.UtcNow.AddSeconds(30);
        while (!File.Exists(descriptorPath))
        {
            if (appHost.HasExited)
            {
                throw new InvalidOperationException(
                    string.Concat(
                        "The disposable Aspire AppHost exited before exact fixture trust became available.",
                        Environment.NewLine,
                        Sanitize(await standardOutput, secrets),
                        Environment.NewLine,
                        Sanitize(await standardError, secrets)));
            }

            if (DateTimeOffset.UtcNow >= deadline)
            {
                throw new TimeoutException(
                    "The exact ephemeral fixture trust descriptor was not created.");
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100), cancellationToken);
        }

        using var descriptor = JsonDocument.Parse(
            await File.ReadAllTextAsync(descriptorPath, cancellationToken));
        var root = descriptor.RootElement;
        Assert.AreEqual(
            string.Concat(
                KeycloakLocalFixtureCatalog.TlsProfile.Identity.Value,
                "@",
                KeycloakLocalFixtureCatalog.TlsProfile.Version.Value),
            root.GetProperty("profile").GetString());
        Assert.AreEqual(
            KeycloakLocalFixtureCatalog.TlsProfile.DotNetTrustMode,
            root.GetProperty("dotNetTrust").GetString());
        Assert.AreEqual(
            KeycloakLocalFixtureCatalog.TlsProfile.ChromiumTrustMode,
            root.GetProperty("chromiumTrust").GetString());
        var relativeAuthorityPath =
            root.GetProperty("authorityCertificate").GetString() ??
            throw new InvalidOperationException(
                "The exact authority certificate path is missing.");
        Assert.AreEqual(
            "tls/authority-certificate.pem",
            relativeAuthorityPath);
        var authorityCertificatePath = Path.GetFullPath(
            Path.Combine(
                runtimeRoot,
                relativeAuthorityPath.Replace(
                    '/',
                    Path.DirectorySeparatorChar)));
        Assert.IsTrue(
            authorityCertificatePath.StartsWith(
                string.Concat(
                    Path.GetFullPath(runtimeRoot).TrimEnd(
                        Path.DirectorySeparatorChar),
                    Path.DirectorySeparatorChar),
                OperatingSystem.IsWindows()
                    ? StringComparison.OrdinalIgnoreCase
                    : StringComparison.Ordinal));
        var chromiumSpkiList =
            root.GetProperty("chromiumSpkiList").GetString() ??
            throw new InvalidOperationException(
                "The exact Chromium SPKI list is missing.");
        Assert.HasCount(
            32,
            Convert.FromBase64String(chromiumSpkiList));
        return new KeycloakFixtureTrust(
            authorityCertificatePath,
            chromiumSpkiList);
    }

    private static SocketsHttpHandler CreateExactTrustHandler(
        string authorityCertificatePath)
    {
        var authority = X509CertificateLoader.LoadCertificateFromFile(
            authorityCertificatePath);
        X509ChainPolicy policy = new()
        {
            TrustMode = X509ChainTrustMode.CustomRootTrust,
            RevocationMode = X509RevocationMode.NoCheck,
            VerificationFlags = X509VerificationFlags.NoFlag,
        };
        policy.CustomTrustStore.Add(authority);
        return new SocketsHttpHandler
        {
            SslOptions = new SslClientAuthenticationOptions
            {
                CertificateChainPolicy = policy,
            },
        };
    }

    private static async Task DeleteDirectoryWithRetryAsync(
        string path,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(15);
        while (true)
        {
            try
            {
                Directory.Delete(path, true);
                return;
            }
            catch (IOException) when (DateTimeOffset.UtcNow < deadline)
            {
                await Task.Delay(
                    TimeSpan.FromMilliseconds(250),
                    cancellationToken);
            }
            catch (UnauthorizedAccessException)
                when (DateTimeOffset.UtcNow < deadline)
            {
                await Task.Delay(
                    TimeSpan.FromMilliseconds(250),
                    cancellationToken);
            }
        }
    }

    private static async Task<string> RequestClientCredentialsAsync(
        HttpClient client,
        string clientId,
        string clientSecret,
        CancellationToken cancellationToken)
    {
        using HttpRequestMessage request = new(
            HttpMethod.Post,
            string.Concat(
                Definition().Authority.AbsoluteUri.TrimEnd('/'),
                "/protocol/openid-connect/token"));
        request.Headers.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/json"));
        request.Content = new FormUrlEncodedContent(
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["grant_type"] = "client_credentials",
                ["client_id"] = clientId,
                ["client_secret"] = clientSecret,
                ["scope"] = Definition().ApiScope,
            });
        using var response = await client.SendAsync(request, cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, response.StatusCode);
        using var document = JsonDocument.Parse(
            await response.Content.ReadAsStreamAsync(cancellationToken));
        Assert.AreEqual(
            "Bearer",
            document.RootElement.GetProperty("token_type").GetString());
        Assert.IsFalse(document.RootElement.TryGetProperty("refresh_token", out _));
        return document.RootElement.GetProperty("access_token").GetString() ??
               throw new InvalidOperationException(
                   "Keycloak returned no client-credentials access token.");
    }

    private static async Task<string> RequestTokenExchangeAsync(
        HttpClient client,
        string subjectToken,
        string clientSecret,
        CancellationToken cancellationToken)
    {
        using HttpRequestMessage request = new(
            HttpMethod.Post,
            string.Concat(
                Definition().Authority.AbsoluteUri.TrimEnd('/'),
                "/protocol/openid-connect/token"));
        request.Content = new FormUrlEncodedContent(
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["grant_type"] =
                    "urn:ietf:params:oauth:grant-type:token-exchange",
                ["client_id"] = Definition().TokenExchangeClientId,
                ["client_secret"] = clientSecret,
                ["subject_token"] = subjectToken,
                ["subject_token_type"] =
                    "urn:ietf:params:oauth:token-type:access_token",
                ["requested_token_type"] =
                    "urn:ietf:params:oauth:token-type:access_token",
                ["scope"] = Definition().ApiScope,
            });
        using var response = await client.SendAsync(request, cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, response.StatusCode);
        using var document = JsonDocument.Parse(
            await response.Content.ReadAsStreamAsync(cancellationToken));
        Assert.AreEqual(
            "urn:ietf:params:oauth:token-type:access_token",
            document.RootElement.GetProperty("issued_token_type").GetString());
        Assert.IsFalse(document.RootElement.TryGetProperty("refresh_token", out _));
        return document.RootElement.GetProperty("access_token").GetString() ??
               throw new InvalidOperationException(
                   "Keycloak returned no exchanged access token.");
    }

    private static async Task<HttpResponseMessage> RequestWrongSecretAsync(
        HttpClient client,
        string clientId,
        CancellationToken cancellationToken)
    {
        using HttpRequestMessage request = new(
            HttpMethod.Post,
            string.Concat(
                Definition().Authority.AbsoluteUri.TrimEnd('/'),
                "/protocol/openid-connect/token"));
        request.Content = new FormUrlEncodedContent(
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["grant_type"] = "client_credentials",
                ["client_id"] = clientId,
                ["client_secret"] = "deliberately-invalid",
                ["scope"] = Definition().ApiScope,
            });
        return await client.SendAsync(request, cancellationToken);
    }

    private static async Task<JsonElement> GetJsonWebKeySetAsync(
        HttpClient client,
        JsonElement metadata,
        CancellationToken cancellationToken)
    {
        var jsonWebKeySetAddress =
            metadata.GetProperty("jwks_uri").GetString() ??
            throw new InvalidOperationException(
                "Keycloak metadata did not contain jwks_uri.");
        using var response = await client.GetAsync(
            jsonWebKeySetAddress,
            cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, response.StatusCode);
        using var document = JsonDocument.Parse(
            await response.Content.ReadAsStreamAsync(cancellationToken));
        Assert.AreNotEqual(
            0,
            document.RootElement.GetProperty("keys").GetArrayLength());
        return document.RootElement.Clone();
    }

    private static HashSet<string> JsonWebKeyIds(JsonElement keySet) =>
        keySet.GetProperty("keys")
            .EnumerateArray()
            .Select(static key =>
                key.GetProperty("kid").GetString() ??
                throw new InvalidOperationException(
                    "A fixture JSON Web Key has no identifier."))
            .ToHashSet(StringComparer.Ordinal);

    private static async Task RotateFixtureSigningKeyAsync(
        HttpClient client,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        using var tokenRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "https://localhost:5443/realms/master/protocol/openid-connect/token")
        {
            Content = new FormUrlEncodedContent(
                new Dictionary<string, string>(StringComparer.Ordinal)
                {
                    ["grant_type"] = "password",
                    ["client_id"] = "admin-cli",
                    ["username"] = "fixture-admin",
                    ["password"] = secrets.AdminPassword,
                }),
        };
        using var tokenResponse = await client.SendAsync(
            tokenRequest,
            cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, tokenResponse.StatusCode);
        using var tokenDocument = JsonDocument.Parse(
            await tokenResponse.Content.ReadAsStreamAsync(cancellationToken));
        var adminToken =
            tokenDocument.RootElement.GetProperty("access_token").GetString() ??
            throw new InvalidOperationException(
                "The disposable provider returned no bounded admin token.");

        using var realmRequest = new HttpRequestMessage(
            HttpMethod.Get,
            "https://localhost:5443/admin/realms/program-kit");
        realmRequest.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", adminToken);
        using var realmResponse = await client.SendAsync(
            realmRequest,
            cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, realmResponse.StatusCode);
        using var realmDocument = JsonDocument.Parse(
            await realmResponse.Content.ReadAsStreamAsync(cancellationToken));
        var realmId = realmDocument.RootElement.GetProperty("id").GetString() ??
            throw new InvalidOperationException(
                "The disposable realm returned no identifier.");

        var component = JsonSerializer.Serialize(
            new
            {
                name = "program-kit-rollover-rsa",
                providerId = "rsa-generated",
                providerType = "org.keycloak.keys.KeyProvider",
                parentId = realmId,
                config = new Dictionary<string, string[]>(StringComparer.Ordinal)
                {
                    ["priority"] = ["200"],
                    ["enabled"] = ["true"],
                    ["active"] = ["true"],
                    ["algorithm"] = ["RS256"],
                    ["keySize"] = ["3072"],
                },
            });
        using var componentRequest = new HttpRequestMessage(
            HttpMethod.Post,
            "https://localhost:5443/admin/realms/program-kit/components")
        {
            Content = new StringContent(
                component,
                Encoding.UTF8,
                "application/json"),
        };
        componentRequest.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", adminToken);
        using var componentResponse = await client.SendAsync(
            componentRequest,
            cancellationToken);
        Assert.IsTrue(
            componentResponse.StatusCode is HttpStatusCode.Created or
                HttpStatusCode.NoContent,
            string.Concat(
                "The disposable signing-key rollover was rejected: ",
                (int)componentResponse.StatusCode));
    }

    private static async Task<HashSet<string>> WaitForJsonWebKeyRolloverAsync(
        HttpClient client,
        JsonElement metadata,
        HashSet<string> initialKeyIds,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(30);
        while (DateTimeOffset.UtcNow < deadline)
        {
            var keySet = await GetJsonWebKeySetAsync(
                client,
                metadata,
                cancellationToken);
            var current = JsonWebKeyIds(keySet);
            if (current.Except(initialKeyIds).Any())
            {
                return current;
            }

            await Task.Delay(
                TimeSpan.FromMilliseconds(250),
                cancellationToken);
        }

        throw new TimeoutException(
            "The disposable provider did not publish the generated rollover key.");
    }

    private static async Task RunGeneratedConfidentialFlowAsync(
        string chromiumSpkiList,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        using var playwright = await Playwright.CreateAsync();
        await using var browser = await playwright.Chromium.LaunchAsync(
            new BrowserTypeLaunchOptions
            {
                Headless = true,
                Args =
                [
                    string.Concat(
                        "--ignore-certificate-errors-spki-list=",
                        chromiumSpkiList),
                ],
            });
        await using var context = await browser.NewContextAsync(
            new BrowserNewContextOptions
            {
                RecordHarPath = null,
                RecordVideoDir = null,
            });
        var page = await context.NewPageAsync();
        var tokenInUrl = false;
        page.Request += (_, request) =>
        {
            tokenInUrl |=
                request.Url.Contains(
                    "access_token=",
                    StringComparison.OrdinalIgnoreCase) ||
                request.Url.Contains(
                    "id_token=",
                    StringComparison.OrdinalIgnoreCase);
        };
        await page.GotoAsync(
            "https://localhost:8443/confidential/login",
            new PageGotoOptions
            {
                WaitUntil = WaitUntilState.DOMContentLoaded,
            });
        await page.Locator("#username").FillAsync(
            Definition().TestPrincipalName);
        await page.Locator("#password").FillAsync(
            secrets.TestPrincipalPassword);
        var callback = page.WaitForURLAsync(
            "https://localhost:8443/confidential/session");
        await page.Locator("#kc-login").ClickAsync();
        await callback;
        Assert.Contains(
            "\"authenticated\":true",
            await page.Locator("body").InnerTextAsync());
        Assert.IsFalse(tokenInUrl);
        var cookies = await context.CookiesAsync(
            ["https://localhost:8443/"]);
        var session = cookies.Single(cookie =>
            cookie.Name == "__Host-program-kit-session");
        Assert.IsTrue(session.HttpOnly);
        Assert.IsTrue(session.Secure);

        await page.GotoAsync(
            "https://localhost:8443/confidential/logout",
            new PageGotoOptions
            {
                WaitUntil = WaitUntilState.DOMContentLoaded,
            });
        var confirmation = page.Locator("#kc-logout");
        if (await confirmation.CountAsync() == 1)
        {
            await confirmation.ClickAsync();
        }

        await page.WaitForURLAsync("https://localhost:8443/");
        Assert.DoesNotContain(
            "__Host-program-kit-session",
            (await context.CookiesAsync(["https://localhost:8443/"]))
            .Select(static cookie => cookie.Name));
        await context.ClearCookiesAsync();
    }

    private static async Task RunGeneratedPublicBrowserFlowAsync(
        string chromiumSpkiList,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        using var playwright = await Playwright.CreateAsync();
        await using var browser = await playwright.Chromium.LaunchAsync(
            new BrowserTypeLaunchOptions
            {
                Headless = true,
                Args =
                [
                    string.Concat(
                        "--ignore-certificate-errors-spki-list=",
                        chromiumSpkiList),
                ],
            });
        await using var context = await browser.NewContextAsync(
            new BrowserNewContextOptions
            {
                RecordHarPath = null,
                RecordVideoDir = null,
            });
        var page = await context.NewPageAsync();
        var tokenInUrl = false;
        page.Request += (_, request) =>
        {
            tokenInUrl |=
                request.Url.Contains(
                    "access_token=",
                    StringComparison.OrdinalIgnoreCase) ||
                request.Url.Contains(
                    "id_token=",
                    StringComparison.OrdinalIgnoreCase);
        };
        await page.GotoAsync(
            "https://localhost:7443/authentication/login?returnUrl=%2Ffixture%2Fprotected-api",
            new PageGotoOptions
            {
                WaitUntil = WaitUntilState.DOMContentLoaded,
            });
        await page.Locator("#username").FillAsync(
            Definition().TestPrincipalName);
        await page.Locator("#password").FillAsync(
            secrets.TestPrincipalPassword);
        var callback = page.WaitForURLAsync(
            "https://localhost:7443/fixture/protected-api");
        await page.Locator("#kc-login").ClickAsync();
        await callback;
        await page.Locator("#call-protected-api").ClickAsync();
        await page.Locator("#protected-api-outcome")
            .WaitForAsync(
                new LocatorWaitForOptions
                {
                    State = WaitForSelectorState.Visible,
                });
        Assert.AreEqual(
            "accepted",
            await page.Locator("#protected-api-outcome").InnerTextAsync());
        Assert.AreEqual(
            0,
            await page.EvaluateAsync<int>(
                "() => window.localStorage.length"));
        Assert.IsFalse(tokenInUrl);

        await page.GotoAsync(
            "https://localhost:7443/authentication/logout?returnUrl=%2F",
            new PageGotoOptions
            {
                WaitUntil = WaitUntilState.DOMContentLoaded,
            });
        var confirmation = page.Locator("#kc-logout");
        if (await confirmation.CountAsync() == 1)
        {
            await confirmation.ClickAsync();
        }

        await page.WaitForURLAsync("https://localhost:7443/");
        Assert.AreEqual(
            0,
            await page.EvaluateAsync<int>(
                "() => window.localStorage.length"));
        await context.ClearCookiesAsync();
        cancellationToken.ThrowIfCancellationRequested();
    }

    private static async Task RunBrowserCodeFlowAsync(
        HttpClient client,
        JsonElement metadata,
        JsonElement jsonWebKeySet,
        string clientId,
        Uri redirectUri,
        string? clientSecret,
        string chromiumSpkiList,
        KeycloakFixtureRuntimeSecrets secrets,
        CancellationToken cancellationToken)
    {
        var verifier = Base64UrlEncode(RandomNumberGenerator.GetBytes(48));
        var challenge = Base64UrlEncode(
            SHA256.HashData(Encoding.ASCII.GetBytes(verifier)));
        var state = Base64UrlEncode(RandomNumberGenerator.GetBytes(24));
        var nonce = Base64UrlEncode(RandomNumberGenerator.GetBytes(24));
        var authorizationEndpoint =
            metadata.GetProperty("authorization_endpoint").GetString() ??
            throw new InvalidOperationException(
                "Keycloak metadata did not contain authorization_endpoint.");
        var authorizationAddress = Query(
            authorizationEndpoint,
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["client_id"] = clientId,
                ["redirect_uri"] = redirectUri.AbsoluteUri,
                ["response_type"] = "code",
                ["scope"] = string.Concat(
                    "openid profile ",
                    Definition().ApiScope),
                ["code_challenge"] = challenge,
                ["code_challenge_method"] = "S256",
                ["state"] = state,
                ["nonce"] = nonce,
            });

        using var playwright = await Playwright.CreateAsync();
        await using var browser = await playwright.Chromium.LaunchAsync(
            new BrowserTypeLaunchOptions
            {
                Headless = true,
                Args =
                [
                    string.Concat(
                        "--ignore-certificate-errors-spki-list=",
                        chromiumSpkiList),
                ],
            });
        await using var context = await browser.NewContextAsync(
            new BrowserNewContextOptions
            {
                RecordHarPath = null,
                RecordVideoDir = null,
            });
        var page = await context.NewPageAsync();
        page.Request += (_, request) =>
        {
            Assert.IsFalse(
                request.Url.Contains(
                    "access_token=",
                    StringComparison.OrdinalIgnoreCase));
            Assert.IsFalse(
                request.Url.Contains(
                    "id_token=",
                    StringComparison.OrdinalIgnoreCase));
        };
        await page.RouteAsync(
            string.Concat(
                redirectUri.GetLeftPart(UriPartial.Authority),
                "/**"),
            static route => route.FulfillAsync(
                new RouteFulfillOptions
                {
                    Status = 200,
                    ContentType = "text/html",
                    Body = "<!doctype html><title>Program Kit callback</title>",
                }));
        await page.GotoAsync(
            authorizationAddress,
            new PageGotoOptions
            {
                WaitUntil = WaitUntilState.DOMContentLoaded,
            });
        await page.Locator("#username").FillAsync(
            Definition().TestPrincipalName);
        await page.Locator("#password").FillAsync(
            secrets.TestPrincipalPassword);
        var callback = page.WaitForURLAsync(
            string.Concat(
                redirectUri.GetLeftPart(UriPartial.Authority),
                "/**"));
        await page.Locator("#kc-login").ClickAsync();
        await callback;

        var callbackUri = new Uri(page.Url);
        var callbackValues = ParseQuery(callbackUri.Query);
        Assert.AreEqual(state, callbackValues["state"]);
        var code = callbackValues["code"];
        Assert.IsFalse(string.IsNullOrWhiteSpace(code));
        Assert.IsFalse(callbackValues.ContainsKey("access_token"));
        Assert.IsFalse(callbackValues.ContainsKey("id_token"));

        var tokenEndpoint =
            metadata.GetProperty("token_endpoint").GetString() ??
            throw new InvalidOperationException(
                "Keycloak metadata did not contain token_endpoint.");
        var tokenFields = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["grant_type"] = "authorization_code",
            ["client_id"] = clientId,
            ["redirect_uri"] = redirectUri.AbsoluteUri,
            ["code"] = code,
            ["code_verifier"] = verifier,
        };
        if (clientSecret is not null)
        {
            tokenFields["client_secret"] = clientSecret;
        }

        using var response = await client.PostAsync(
            tokenEndpoint,
            new FormUrlEncodedContent(tokenFields),
            cancellationToken);
        Assert.AreEqual(HttpStatusCode.OK, response.StatusCode);
        using var tokenDocument = JsonDocument.Parse(
            await response.Content.ReadAsStreamAsync(cancellationToken));
        var accessToken =
            tokenDocument.RootElement.GetProperty("access_token").GetString() ??
            throw new InvalidOperationException(
                "Keycloak returned no authorization-code access token.");
        var idToken =
            tokenDocument.RootElement.GetProperty("id_token").GetString() ??
            throw new InvalidOperationException(
                "Keycloak returned no authorization-code ID token.");
        VerifyAccessToken(accessToken, Definition(), jsonWebKeySet);
        VerifyIdToken(idToken, clientId, nonce, Definition(), jsonWebKeySet);

        using var replay = await client.PostAsync(
            tokenEndpoint,
            new FormUrlEncodedContent(tokenFields),
            cancellationToken);
        Assert.AreEqual(HttpStatusCode.BadRequest, replay.StatusCode);

        Assert.AreEqual(
            0,
            await page.EvaluateAsync<int>(
                "() => window.localStorage.length"));
        Assert.AreEqual(
            0,
            await page.EvaluateAsync<int>(
                "() => window.sessionStorage.length"));
        await context.ClearCookiesAsync();
    }

    private static string Query(
        string baseAddress,
        IReadOnlyDictionary<string, string> values) =>
        string.Concat(
            baseAddress,
            "?",
            string.Join(
                "&",
                values.OrderBy(
                        static item => item.Key,
                        StringComparer.Ordinal)
                    .Select(static item => string.Concat(
                        Uri.EscapeDataString(item.Key),
                        "=",
                        Uri.EscapeDataString(item.Value)))));

    private static Dictionary<string, string> ParseQuery(string query)
    {
        Dictionary<string, string> values = new(StringComparer.Ordinal);
        foreach (var pair in query.TrimStart('?').Split(
                     '&',
                     StringSplitOptions.RemoveEmptyEntries))
        {
            var separator = pair.IndexOf('=');
            var name = separator < 0 ? pair : pair[..separator];
            var value = separator < 0 ? string.Empty : pair[(separator + 1)..];
            values.Add(
                Uri.UnescapeDataString(name.Replace('+', ' ')),
                Uri.UnescapeDataString(value.Replace('+', ' ')));
        }

        return values;
    }

    private static void VerifyAccessToken(
        string token,
        KeycloakLocalFixtureDefinition definition,
        JsonElement jsonWebKeySet)
    {
        var segments = token.Split('.');
        Assert.HasCount(3, segments);
        using var header = JsonDocument.Parse(Base64UrlDecode(segments[0]));
        using var payload = JsonDocument.Parse(Base64UrlDecode(segments[1]));
        Assert.AreEqual(
            "at+jwt",
            header.RootElement.GetProperty("typ").GetString());
        Assert.AreEqual(
            "RS256",
            header.RootElement.GetProperty("alg").GetString());
        Assert.AreEqual(
            definition.Authority.AbsoluteUri.TrimEnd('/'),
            payload.RootElement.GetProperty("iss").GetString());
        var audiences = payload.RootElement.GetProperty("aud").ValueKind ==
                        JsonValueKind.Array
            ? payload.RootElement.GetProperty("aud").EnumerateArray()
                .Select(static item => item.GetString())
                .ToArray()
            : [payload.RootElement.GetProperty("aud").GetString()];
        Assert.Contains(definition.ApiAudience, audiences);
        Assert.IsGreaterThan(
            DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            payload.RootElement.GetProperty("exp").GetInt64());
        VerifySignature(segments, header.RootElement, jsonWebKeySet);
    }

    private static void VerifyIdToken(
        string token,
        string clientId,
        string nonce,
        KeycloakLocalFixtureDefinition definition,
        JsonElement jsonWebKeySet)
    {
        var segments = token.Split('.');
        Assert.HasCount(3, segments);
        using var header = JsonDocument.Parse(Base64UrlDecode(segments[0]));
        using var payload = JsonDocument.Parse(Base64UrlDecode(segments[1]));
        Assert.AreEqual(
            "JWT",
            header.RootElement.GetProperty("typ").GetString());
        Assert.AreEqual(
            "RS256",
            header.RootElement.GetProperty("alg").GetString());
        Assert.AreEqual(
            definition.Authority.AbsoluteUri.TrimEnd('/'),
            payload.RootElement.GetProperty("iss").GetString());
        Assert.AreEqual(
            clientId,
            payload.RootElement.GetProperty("aud").GetString());
        Assert.AreEqual(
            nonce,
            payload.RootElement.GetProperty("nonce").GetString());
        Assert.IsGreaterThan(
            DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            payload.RootElement.GetProperty("exp").GetInt64());
        VerifySignature(segments, header.RootElement, jsonWebKeySet);
    }

    private static void VerifySignature(
        string[] segments,
        JsonElement header,
        JsonElement jsonWebKeySet)
    {
        var keyId = header.GetProperty("kid").GetString();
        var key = jsonWebKeySet.GetProperty("keys")
            .EnumerateArray()
            .Single(candidate =>
                string.Equals(
                    candidate.GetProperty("kid").GetString(),
                    keyId,
                    StringComparison.Ordinal) &&
                string.Equals(
                    candidate.GetProperty("kty").GetString(),
                    "RSA",
                    StringComparison.Ordinal));
        using var algorithm = RSA.Create();
        algorithm.ImportParameters(
            new RSAParameters
            {
                Modulus = Base64UrlDecode(key.GetProperty("n").GetString()!),
                Exponent = Base64UrlDecode(key.GetProperty("e").GetString()!),
            });
        Assert.IsTrue(
            algorithm.VerifyData(
                Encoding.ASCII.GetBytes(
                    string.Concat(segments[0], ".", segments[1])),
                Base64UrlDecode(segments[2]),
                HashAlgorithmName.SHA256,
                RSASignaturePadding.Pkcs1),
            "The token signature did not verify against the discovered JWKS.");
    }

    private static byte[] Base64UrlDecode(string value)
    {
        var padded = value.Replace('-', '+').Replace('_', '/');
        padded = padded.PadRight(
            padded.Length + ((4 - (padded.Length % 4)) % 4),
            '=');
        return Convert.FromBase64String(padded);
    }

    private static string Base64UrlEncode(ReadOnlySpan<byte> value) =>
        Convert.ToBase64String(value)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');

    private static KeycloakFixtureRuntimeSecrets CreateRuntimeSecrets() =>
        new(
            RandomSecret(),
            RandomSecret(),
            RandomSecret(),
            RandomSecret(),
            RandomSecret());

    private static string RandomSecret() =>
        Convert.ToBase64String(RandomNumberGenerator.GetBytes(36));

    private static string Sanitize(
        string value,
        KeycloakFixtureRuntimeSecrets secrets)
    {
        var sanitized = value;
        foreach (var secret in secrets.All)
        {
            sanitized = sanitized.Replace(
                secret,
                "[REDACTED]",
                StringComparison.Ordinal);
        }

        return Regex.Replace(
            sanitized,
            @"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "[REDACTED-JWT]",
            RegexOptions.CultureInvariant,
            TimeSpan.FromSeconds(1));
    }

    private const string TlsProbeProject =
        """
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <OutputType>Exe</OutputType>
            <TargetFramework>net10.0</TargetFramework>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <LangVersion>14.0</LangVersion>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <EnableNETAnalyzers>true</EnableNETAnalyzers>
            <AnalysisLevel>latest-all</AnalysisLevel>
          </PropertyGroup>
        </Project>
        """;

    private const string TlsProbeProgram =
        """
        var runtimeRoot = args.Single();
        using var cancelled = new global::System.Threading.CancellationTokenSource();
        await cancelled.CancelAsync().ConfigureAwait(false);
        try
        {
            _ = await global::ProgramKitFixtureTls.CreateAsync(
                runtimeRoot,
                cancelled.Token).ConfigureAwait(false);
            throw new global::System.InvalidOperationException(
                "Cancelled creation unexpectedly succeeded.");
        }
        catch (global::System.OperationCanceledException)
        {
        }

        if (global::System.IO.Directory.Exists(
                global::System.IO.Path.Combine(runtimeRoot, "tls")))
        {
            throw new global::System.InvalidOperationException(
                "Cancelled creation retained owned TLS state.");
        }

        var fixture = await global::ProgramKitFixtureTls.CreateAsync(
            runtimeRoot,
            global::System.Threading.CancellationToken.None).ConfigureAwait(false);
        try
        {
            using var authority =
                global::System.Security.Cryptography.X509Certificates.X509CertificateLoader.LoadCertificateFromFile(
                    fixture.AuthorityCertificatePath);
            using var server =
                global::System.Security.Cryptography.X509Certificates.X509CertificateLoader.LoadCertificateFromFile(
                    fixture.ServerCertificatePath);
            var authorityConstraints = authority.Extensions
                .OfType<global::System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension>()
                .Single();
            if (!authorityConstraints.CertificateAuthority ||
                !authorityConstraints.HasPathLengthConstraint ||
                authorityConstraints.PathLengthConstraint != 0)
            {
                throw new global::System.InvalidOperationException(
                    "The fixture authority constraints differ.");
            }

            using var authorityKey =
                global::System.Security.Cryptography.X509Certificates.RSACertificateExtensions.GetRSAPublicKey(
                    authority);
            using var serverKey =
                global::System.Security.Cryptography.X509Certificates.RSACertificateExtensions.GetRSAPublicKey(
                    server);
            if (authorityKey?.KeySize != 3072 ||
                serverKey?.KeySize != 3072 ||
                server.HasPrivateKey)
            {
                throw new global::System.InvalidOperationException(
                    "The fixture public certificate key profile differs.");
            }

            var authorityUsage = authority.Extensions
                .OfType<global::System.Security.Cryptography.X509Certificates.X509KeyUsageExtension>()
                .Single()
                .KeyUsages;
            if (!authorityUsage.HasFlag(
                    global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.KeyCertSign) ||
                !authorityUsage.HasFlag(
                    global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.CrlSign))
            {
                throw new global::System.InvalidOperationException(
                    "The fixture authority key usage differs.");
            }

            var serverUsage = server.Extensions
                .OfType<global::System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension>()
                .Single()
                .EnhancedKeyUsages
                .Cast<global::System.Security.Cryptography.Oid>()
                .Select(static usage => usage.Value)
                .ToArray();
            if (!serverUsage.Contains(
                    "1.3.6.1.5.5.7.3.1",
                    global::System.StringComparer.Ordinal) ||
                !string.Equals(
                    server.GetNameInfo(
                        global::System.Security.Cryptography.X509Certificates.X509NameType.DnsName,
                        forIssuer: false),
                    "localhost",
                    global::System.StringComparison.Ordinal) ||
                server.NotAfter.ToUniversalTime() >
                    server.NotBefore.ToUniversalTime().AddHours(8).AddMinutes(1) ||
                authority.NotAfter.ToUniversalTime() >
                    authority.NotBefore.ToUniversalTime().AddHours(24).AddMinutes(1))
            {
                throw new global::System.InvalidOperationException(
                    "The fixture server identity or validity profile differs.");
            }

            using var chain =
                new global::System.Security.Cryptography.X509Certificates.X509Chain();
            chain.ChainPolicy.TrustMode =
                global::System.Security.Cryptography.X509Certificates.X509ChainTrustMode.CustomRootTrust;
            chain.ChainPolicy.RevocationMode =
                global::System.Security.Cryptography.X509Certificates.X509RevocationMode.NoCheck;
            chain.ChainPolicy.VerificationFlags =
                global::System.Security.Cryptography.X509Certificates.X509VerificationFlags.NoFlag;
            chain.ChainPolicy.ApplicationPolicy.Add(
                new global::System.Security.Cryptography.Oid(
                    "1.3.6.1.5.5.7.3.1",
                    "TLS Web Server Authentication"));
            chain.ChainPolicy.CustomTrustStore.Add(authority);
            if (!chain.Build(server))
            {
                throw new global::System.InvalidOperationException(
                    "The exact custom-root chain did not validate.");
            }

            using var substitutedKey =
                global::System.Security.Cryptography.RSA.Create(3072);
            var substitutedRequest =
                new global::System.Security.Cryptography.X509Certificates.CertificateRequest(
                    "CN=localhost",
                    substitutedKey,
                    global::System.Security.Cryptography.HashAlgorithmName.SHA256,
                    global::System.Security.Cryptography.RSASignaturePadding.Pkcs1);
            substitutedRequest.CertificateExtensions.Add(
                new global::System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension(
                    certificateAuthority: false,
                    hasPathLengthConstraint: false,
                    pathLengthConstraint: 0,
                    critical: true));
            using var substituted = substitutedRequest.CreateSelfSigned(
                global::System.DateTimeOffset.UtcNow.AddMinutes(-1),
                global::System.DateTimeOffset.UtcNow.AddMinutes(10));
            using var substitutedChain =
                new global::System.Security.Cryptography.X509Certificates.X509Chain();
            substitutedChain.ChainPolicy.TrustMode =
                global::System.Security.Cryptography.X509Certificates.X509ChainTrustMode.CustomRootTrust;
            substitutedChain.ChainPolicy.RevocationMode =
                global::System.Security.Cryptography.X509Certificates.X509RevocationMode.NoCheck;
            substitutedChain.ChainPolicy.CustomTrustStore.Add(authority);
            if (substitutedChain.Build(substituted))
            {
                throw new global::System.InvalidOperationException(
                    "A substituted self-signed server certificate was accepted.");
            }

            var expectedSpki = global::System.Convert.ToBase64String(
                global::System.Security.Cryptography.SHA256.HashData(
                    serverKey.ExportSubjectPublicKeyInfo()));
            var actualSpki =
                global::ProgramKitFixtureTrust.ReadChromiumSpkiList(runtimeRoot);
            if (!string.Equals(
                    expectedSpki,
                    actualSpki,
                    global::System.StringComparison.Ordinal))
            {
                throw new global::System.InvalidOperationException(
                    "The exact Chromium SPKI binding differs.");
            }

            using var handler =
                global::ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot);
            if (handler.SslOptions.CertificateChainPolicy?.TrustMode !=
                    global::System.Security.Cryptography.X509Certificates.X509ChainTrustMode.CustomRootTrust ||
                handler.SslOptions.CertificateChainPolicy.CustomTrustStore.Count != 1)
            {
                throw new global::System.InvalidOperationException(
                    "The exact .NET custom-root trust policy differs.");
            }

            try
            {
                _ = await global::ProgramKitFixtureTls.CreateAsync(
                    runtimeRoot,
                    global::System.Threading.CancellationToken.None).ConfigureAwait(false);
                throw new global::System.InvalidOperationException(
                    "An existing TLS directory was reused.");
            }
            catch (global::System.InvalidOperationException exception)
                when (exception.Message.Contains(
                    "already exists",
                    global::System.StringComparison.Ordinal))
            {
            }
        }
        finally
        {
            await fixture.DisposeAsync().ConfigureAwait(false);
        }

        if (global::System.IO.Directory.Exists(
                global::System.IO.Path.Combine(runtimeRoot, "tls")))
        {
            throw new global::System.InvalidOperationException(
                "Bounded disposal retained owned TLS state.");
        }

        """;

    private static async Task WaitForOwnedContainersToStopAsync(
        ImmutableHashSet<string> baseline,
        CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow.AddSeconds(30);
        while (DateTimeOffset.UtcNow < deadline)
        {
            var current = await GetKeycloakContainerIdsAsync(cancellationToken);
            if (current.IsSubsetOf(baseline))
            {
                return;
            }

            await Task.Delay(TimeSpan.FromSeconds(1), cancellationToken);
        }

        Assert.Fail(
            "The disposable Keycloak container remained after AppHost teardown.");
    }

    private static async Task<ImmutableHashSet<string>> GetKeycloakContainerIdsAsync(
        CancellationToken cancellationToken)
    {
        ProcessStartInfo startInfo = new("docker")
        {
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        startInfo.ArgumentList.Add("ps");
        startInfo.ArgumentList.Add("--filter");
        startInfo.ArgumentList.Add("ancestor=quay.io/keycloak/keycloak:26.7.0");
        startInfo.ArgumentList.Add("--format");
        startInfo.ArgumentList.Add("{{.ID}}");
        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                "The bounded Docker inspection did not start.");
        var output = await process.StandardOutput.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);
        Assert.AreEqual(0, process.ExitCode);
        return output.Split(
                ['\r', '\n'],
                StringSplitOptions.RemoveEmptyEntries |
                StringSplitOptions.TrimEntries)
            .ToImmutableHashSet(StringComparer.Ordinal);
    }

    private static string FindProgramKitPath(params string[] parts)
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null &&
               !File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
        {
            current = current.Parent;
        }

        if (current is null)
        {
            throw new DirectoryNotFoundException(
                "The Program Kit root could not be resolved.");
        }

        return Path.Combine([current.FullName, .. parts]);
    }

    private const string NuGetConfiguration =
        """
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <packageSources>
            <clear />
            <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
          </packageSources>
          <packageSourceMapping>
            <clear />
            <packageSource key="nuget.org">
              <package pattern="*" />
            </packageSource>
          </packageSourceMapping>
        </configuration>
        """;

}
