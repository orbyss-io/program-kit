using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Providers.DotNet.Composition.HttpEndpoints;
using Orbyss.ProgramKit.Providers.DotNet.Construction;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;
using Orbyss.ProgramKit.Providers.DotNet.Templates;

namespace Orbyss.ProgramKit.Providers.DotNet;

internal sealed class DotNetFactoryProvider
{
    private readonly DotNetToolRunner tools = new();

    public ProviderManifest Manifest { get; } = DotNetProviderManifest.Create();

    public async Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context)
    {
        try
        {
            JsonObject component = RequireObject(context.Definition, "component");
            JsonObject application = RequireObject(context.Definition, "application");
            string componentName = Required(component, "name");
            string applicationName = Required(application, "name");
            string packageId = Required(component, "packageId");
            string packageVersion = Required(component, "version");
            string implementationSource = Required(component, "implementationSource");
            string route = Required(application, "route");
            string method = Required(application, "method");
            EndpointAssembler.Resolve(new[]
            {
                new EndpointContribution($"{applicationName}:{method}:{route}", method, route, Required(component, "featureClass"), null),
            });

            ValidatedMirror mirror = ValidateDependencyMirror(context.DependencyMirrorRoot);
            string componentRoot = Path.Combine(context.CandidateRoot, "products", componentName);
            string applicationRoot = Path.Combine(context.CandidateRoot, "products", applicationName);
            string componentFeed = Path.Combine(context.CandidateRoot, "feeds", "component");
            string dependencyFeed = Path.Combine(context.CandidateRoot, "feeds", "dependencies");
            string packagesRoot = Path.Combine(context.CandidateRoot, ".packages");
            Directory.CreateDirectory(componentRoot);
            Directory.CreateDirectory(applicationRoot);
            Directory.CreateDirectory(componentFeed);
            CopyValidatedMirror(context.DependencyMirrorRoot, dependencyFeed, mirror);

            WriteUtf8(Path.Combine(componentRoot, $"{componentName}.csproj"), DotNetTemplates.ComponentProject(component));
            string sourcePath = ResolveConsumerSource(context.WorkspaceRoot, implementationSource);
            File.Copy(sourcePath, Path.Combine(componentRoot, Path.GetFileName(sourcePath)), overwrite: false);
            string componentConfig = Path.Combine(componentRoot, "NuGet.Config");
            WriteUtf8(componentConfig, DotNetTemplates.NuGetConfig(packageId, "../../feeds/component", "../../feeds/dependencies"));

            ToolObservation componentRestore = await tools.RunAsync(componentRoot, new[]
            {
                "restore", $"{componentName}.csproj", "--configfile", componentConfig, "--packages", packagesRoot, "--no-cache", "--use-lock-file",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!componentRestore.Succeeded)
            {
                return Failure(DiagnosticIds.DotNetToolFailure, componentRestore);
            }

            ToolObservation lockedRestore = await tools.RunAsync(componentRoot, new[]
            {
                "restore", $"{componentName}.csproj", "--configfile", componentConfig, "--packages", packagesRoot, "--no-cache", "--locked-mode",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!lockedRestore.Succeeded)
            {
                return Failure(DiagnosticIds.DotNetToolFailure, lockedRestore);
            }

            ToolObservation componentBuild = await tools.RunAsync(componentRoot, new[]
            {
                "build", $"{componentName}.csproj", "--configuration", "Release", "--no-restore",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!componentBuild.Succeeded)
            {
                return Failure(DiagnosticIds.CShellsConformance, componentBuild);
            }

            ToolObservation componentPack = await tools.RunAsync(componentRoot, new[]
            {
                "pack", $"{componentName}.csproj", "--configuration", "Release", "--no-build", "--no-restore", "--output", componentFeed,
            }, context.CancellationToken).ConfigureAwait(false);
            if (!componentPack.Succeeded)
            {
                return Failure(DiagnosticIds.DotNetToolFailure, componentPack);
            }

            string packagePath = Path.Combine(componentFeed, $"{packageId}.{packageVersion}.nupkg");
            if (!File.Exists(packagePath))
            {
                return new ProviderConstructionResult(Array.Empty<ProviderArtifact>(), Array.Empty<JsonObject>(), new[] { DiagnosticIds.PackageMismatch }, false);
            }

            byte[] packageBytes = File.ReadAllBytes(packagePath);
            string packageDigest = Digest(packageBytes);
            string nugetContentHash = Convert.ToBase64String(SHA512.HashData(packageBytes));
            WriteUtf8(Path.Combine(applicationRoot, $"{applicationName}.csproj"), DotNetTemplates.ApplicationProject(application, component));
            WriteUtf8(Path.Combine(applicationRoot, "Program.cs"), DotNetTemplates.ProgramSource(component));
            WriteUtf8(Path.Combine(applicationRoot, "appsettings.json"), DotNetTemplates.AppSettings(component));
            string applicationConfig = Path.Combine(applicationRoot, "NuGet.Config");
            WriteUtf8(applicationConfig, DotNetTemplates.NuGetConfig(packageId, "../../feeds/component", "../../feeds/dependencies"));

            JsonObject packageLock = new()
            {
                ["nugetContentHash"] = nugetContentHash,
                ["digest"] = packageDigest,
                ["packageId"] = packageId,
                ["producerConstructionIdentity"] = context.ConstructionIdentity,
                ["schema"] = "program-kit.package-binding/v1",
                ["version"] = packageVersion,
            };
            WriteUtf8(Path.Combine(applicationRoot, "program-kit.package-binding.json"), Canonical(packageLock));

            ToolObservation applicationRestore = await tools.RunAsync(applicationRoot, new[]
            {
                "restore", $"{applicationName}.csproj", "--configfile", applicationConfig, "--packages", packagesRoot, "--no-cache", "--use-lock-file",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!applicationRestore.Succeeded)
            {
                return Failure(DiagnosticIds.DotNetToolFailure, applicationRestore);
            }

            ToolObservation applicationLockedRestore = await tools.RunAsync(applicationRoot, new[]
            {
                "restore", $"{applicationName}.csproj", "--configfile", applicationConfig, "--packages", packagesRoot, "--no-cache", "--locked-mode",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!applicationLockedRestore.Succeeded)
            {
                return Failure(DiagnosticIds.DotNetToolFailure, applicationLockedRestore);
            }

            ToolObservation applicationBuild = await tools.RunAsync(applicationRoot, new[]
            {
                "build", $"{applicationName}.csproj", "--configuration", "Release", "--no-restore",
            }, context.CancellationToken).ConfigureAwait(false);
            if (!applicationBuild.Succeeded)
            {
                return Failure(DiagnosticIds.CShellsConformance, applicationBuild);
            }

            RemoveTransientDirectories(context.CandidateRoot);
            ProviderArtifact[] artifacts = Directory.EnumerateFiles(context.CandidateRoot, "*", SearchOption.AllDirectories)
                .Where(path => !Path.GetRelativePath(context.CandidateRoot, path).Replace('\\', '/')
                    .StartsWith(".program-kit/", StringComparison.Ordinal))
                .Select(path => new ProviderArtifact(
                    Path.GetRelativePath(context.CandidateRoot, path).Replace('\\', '/'),
                    path.EndsWith(Path.GetFileName(sourcePath), StringComparison.Ordinal) ? ArtifactOwnership.SeededHandoff : ArtifactOwnership.GeneratedOwned,
                    MediaType(path),
                    path.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase)
                        || path.EndsWith("packages.lock.json", StringComparison.Ordinal)
                        || path.EndsWith("program-kit.package-binding.json", StringComparison.Ordinal)
                            ? ClaimClass.VerifiedEquivalent : path.EndsWith(Path.GetFileName(sourcePath), StringComparison.Ordinal) ? ClaimClass.CustomBounded : ClaimClass.CanonicalByte,
                    Manifest.Identity.StableKey))
                .OrderBy(static item => item.LogicalPath, StringComparer.Ordinal)
                .ToArray();
            JsonObject evidence = new()
            {
                ["provider"] = Manifest.Identity.StableKey,
                ["profile"] = DotNetProviderManifest.Profile,
                ["nugetContentHash"] = nugetContentHash,
                ["mirrorLockDigest"] = mirror.LockDigest,
                ["packageDigest"] = packageDigest,
                ["componentRestore"] = componentRestore.OutputDigest,
                ["componentBuild"] = componentBuild.OutputDigest,
                ["componentPack"] = componentPack.OutputDigest,
                ["applicationRestore"] = applicationRestore.OutputDigest,
                ["applicationBuild"] = applicationBuild.OutputDigest,
            };
            return new ProviderConstructionResult(artifacts, new[] { evidence }, Array.Empty<string>(), true);
        }
        catch (InvalidOperationException exception) when (exception.Message.StartsWith("Duplicate route", StringComparison.Ordinal))
        {
            return new ProviderConstructionResult(Array.Empty<ProviderArtifact>(), Array.Empty<JsonObject>(), new[] { DiagnosticIds.DuplicateRoute }, false);
        }
        catch (Exception)
        {
            return new ProviderConstructionResult(Array.Empty<ProviderArtifact>(), Array.Empty<JsonObject>(), new[] { DiagnosticIds.DotNetToolFailure }, false);
        }
    }

    private static ProviderConstructionResult Failure(string diagnosticId, ToolObservation observation) =>
        new(Array.Empty<ProviderArtifact>(), new[]
        {
            new JsonObject
            {
                ["tool"] = observation.Tool,
                ["arguments"] = new JsonArray(observation.Arguments.Select(static value => JsonValue.Create(value)).ToArray()),
                ["observationDigest"] = observation.OutputDigest,
                ["diagnosticCodes"] = new JsonArray(observation.DiagnosticCodes.Select(static value => JsonValue.Create(value)).ToArray()),
                ["exitCode"] = observation.ExitCode,
            },
        }, new[] { diagnosticId }, false);

    private static string ResolveConsumerSource(string workspaceRoot, string logicalPath)
    {
        string root = Path.GetFullPath(workspaceRoot).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string path = Path.GetFullPath(Path.Combine(root, logicalPath.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
        {
            throw new InvalidOperationException("Consumer implementation source is missing or outside the workspace.");
        }

        return path;
    }

    private static ValidatedMirror ValidateDependencyMirror(string source)
    {
        if (!Directory.Exists(source) || (File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0
            || Directory.EnumerateDirectories(source).Any())
        {
            throw new InvalidOperationException("The governed dependency mirror is unavailable or not a closed directory.");
        }

        string lockPath = Path.Combine(source, "mirror.lock.json");
        if (!File.Exists(lockPath) || (File.GetAttributes(lockPath) & FileAttributes.ReparsePoint) != 0)
        {
            throw new InvalidOperationException("The governed dependency mirror lock is unavailable.");
        }

        byte[] lockBytes = File.ReadAllBytes(lockPath);
        using JsonDocument parsed = JsonDocument.Parse(lockBytes, new JsonDocumentOptions
        {
            AllowDuplicateProperties = false,
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow,
            MaxDepth = 32,
        });
        JsonObject document = JsonNode.Parse(parsed.RootElement.GetRawText()) as JsonObject
            ?? throw new InvalidOperationException("The governed dependency mirror lock must be an object.");
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.dependency-mirror-lock/v1", StringComparison.Ordinal)
            || document["packages"] is not JsonArray packages
            || packages.Count == 0)
        {
            throw new InvalidOperationException("The governed dependency mirror lock has an unsupported contract.");
        }

        List<MirrorArtifact> expected = new();
        foreach (JsonObject package in packages.OfType<JsonObject>())
        {
            string id = Required(package, "id");
            string version = Required(package, "version");
            string digest = Required(package, "sha256");
            string fileName = $"{id.ToLowerInvariant()}.{version}.nupkg";
            string path = Path.Combine(source, fileName);
            if (!File.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0
                || !string.Equals(Digest(File.ReadAllBytes(path)), digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Dependency mirror artifact is missing or changed: {fileName}");
            }

            expected.Add(new MirrorArtifact(fileName, digest));
        }

        if (expected.Select(static item => item.FileName).Distinct(StringComparer.OrdinalIgnoreCase).Count() != expected.Count)
        {
            throw new InvalidOperationException("The governed dependency mirror lock contains duplicate package identities.");
        }

        string[] expectedFiles = expected.Select(static item => item.FileName).Append("mirror.lock.json").OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        string[] actualFiles = Directory.EnumerateFiles(source).Select(Path.GetFileName).OrderBy(static item => item, StringComparer.Ordinal).ToArray()!;
        if (!expectedFiles.SequenceEqual(actualFiles, StringComparer.Ordinal))
        {
            throw new InvalidOperationException("The governed dependency mirror contains undeclared, missing, or case-colliding artifacts.");
        }

        expected.Add(new MirrorArtifact("mirror.lock.json", Digest(lockBytes)));
        return new ValidatedMirror(Digest(lockBytes), expected.OrderBy(static item => item.FileName, StringComparer.Ordinal).ToArray());
    }

    private static void CopyValidatedMirror(string source, string destination, ValidatedMirror mirror)
    {
        Directory.CreateDirectory(destination);
        foreach (MirrorArtifact artifact in mirror.Artifacts)
        {
            byte[] bytes = File.ReadAllBytes(Path.Combine(source, artifact.FileName));
            if (!string.Equals(Digest(bytes), artifact.Digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Dependency mirror artifact changed during construction: {artifact.FileName}");
            }

            string target = Path.Combine(destination, artifact.FileName);
            File.WriteAllBytes(target, bytes);
            if (!string.Equals(Digest(File.ReadAllBytes(target)), artifact.Digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Dependency mirror artifact copy verification failed: {artifact.FileName}");
            }
        }
    }

    private sealed record MirrorArtifact(string FileName, string Digest);

    private sealed record ValidatedMirror(string LockDigest, IReadOnlyList<MirrorArtifact> Artifacts);

    private static void RemoveTransientDirectories(string root)
    {
        foreach (string path in Directory.EnumerateDirectories(root, "*", SearchOption.AllDirectories)
            .Where(static path => string.Equals(Path.GetFileName(path), "bin", StringComparison.OrdinalIgnoreCase)
                || string.Equals(Path.GetFileName(path), "obj", StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(static path => path.Length))
        {
            if (Directory.Exists(path))
            {
                Directory.Delete(path, recursive: true);
            }
        }

        string packages = Path.Combine(root, ".packages");
        if (Directory.Exists(packages))
        {
            Directory.Delete(packages, recursive: true);
        }
    }

    private static JsonObject RequireObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidOperationException($"definition.{name} must be an object.");

    private static string Required(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidOperationException($"definition field {name} is required.");

    private static void WriteUtf8(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, content.Replace("\r\n", "\n", StringComparison.Ordinal), new UTF8Encoding(false));
    }

    private static string Digest(byte[] bytes) => $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";

    private static string Canonical(JsonObject value)
    {
        using MemoryStream stream = new();
        using (System.Text.Json.Utf8JsonWriter writer = new(stream, new System.Text.Json.JsonWriterOptions { Indented = false }))
        {
            value.WriteTo(writer);
        }

        return Encoding.UTF8.GetString(stream.ToArray());
    }

    private static string MediaType(string path) => Path.GetExtension(path).ToLowerInvariant() switch
    {
        ".json" => "application/json",
        ".nupkg" => "application/vnd.nuget.package",
        ".cs" => "text/x-csharp",
        ".csproj" => "application/xml",
        ".config" => "application/xml",
        _ => "application/octet-stream",
    };
}
