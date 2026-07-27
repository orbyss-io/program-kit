using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;
using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;
using Orbyss.ProgramKit.DevContainers.Contracts.Diagnostics;
using Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;
using Orbyss.ProgramKit.DevContainers.Contracts.Mounts;
using Orbyss.ProgramKit.DevContainers.Contracts.Profiles;
using Orbyss.ProgramKit.DevContainers.Operations.Validation;

namespace Orbyss.ProgramKit.DevContainers.Operations.Generation;

/// <summary>
/// Deterministic non-executing generator for the reviewed Dev Container base
/// profile.
/// </summary>
public sealed class DevContainerGenerator : IDevContainerGenerator
{
    private const string BaseSchemaUri =
        "https://raw.githubusercontent.com/devcontainers/spec/c95ffeed1d059abfe9ffbe79762dc2fa4e7c2421/schemas/devContainer.base.schema.json";
    private const string BaseSchemaSha256 =
        "sha256:a0883c0405ff433db188849d458fb20b9c0d73e0ba1a6e44c1d83f3b485408dd";
    private const string SpecificationCommit =
        "c95ffeed1d059abfe9ffbe79762dc2fa4e7c2421";
    private const string DesignSha256 =
        "sha256:a9ad015470f3996ea09811d57007ec4ab90e3b2cbff91245e625bfdd82ad0d57";
    private const string PlanSha256 =
        "sha256:8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5";
    private readonly IDevContainerDefinitionValidator validator;

    /// <summary>Initializes the generator with an explicit validator.</summary>
    public DevContainerGenerator(IDevContainerDefinitionValidator validator)
    {
        this.validator = validator ?? throw new ArgumentNullException(nameof(validator));
    }

    /// <inheritdoc />
    public DevContainerGenerationResult Generate(
        DevContainerDefinition definition,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(definition);
        cancellationToken.ThrowIfCancellationRequested();
        var validation = validator.Validate(definition);
        if (!validation.IsValid)
        {
            var diagnostic = validation.Diagnostics.First(item =>
                item.Severity == ProgramKitDiagnosticSeverity.Error);
            throw new DevContainerGenerationException(
                diagnostic.Id,
                diagnostic.Path,
                diagnostic.Message);
        }

        var files = ImmutableArray.CreateBuilder<DevContainerGeneratedFile>();
        files.Add(new DevContainerGeneratedFile(
            ".devcontainer/devcontainer.json",
            Bytes(RenderDevContainer(definition, cancellationToken))));

        switch (definition.Profile)
        {
            case DevContainerDockerfileProfile dockerfile:
                AddOpaque(files, dockerfile.Dockerfile);
                break;
            case DevContainerComposeProfile compose:
                if (compose.Dockerfile is not null)
                {
                    AddOpaque(files, compose.Dockerfile);
                }

                files.Add(new DevContainerGeneratedFile(
                    ".devcontainer/compose.yaml",
                    Bytes(RenderCompose(compose))));
                break;
        }

        foreach (var script in definition.Scripts.OrderBy(
                     static item => item.RelativePath,
                     StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();
            AddOpaque(files, script);
        }

        var ordered = files
            .OrderBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        EnsureUniquePaths(ordered);
        var inputDigest = Digest(RenderInputEvidence(definition));
        var lockBytes = RenderLock(definition, inputDigest, ordered);
        ordered = ordered
            .Add(new DevContainerGeneratedFile(
                ".devcontainer/devcontainer.lock.json",
                lockBytes))
            .OrderBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        cancellationToken.ThrowIfCancellationRequested();
        return new DevContainerGenerationResult(ordered, TreeDigest(ordered));
    }

    private static byte[] RenderDevContainer(
        DevContainerDefinition definition,
        CancellationToken cancellationToken)
    {
        return WriteJson(writer =>
        {
            writer.WriteStartObject();
            writer.WriteString("$schema", BaseSchemaUri);
            writer.WriteString("name", definition.Name);
            RenderProfile(writer, definition.Profile);
            if (!definition.Features.IsEmpty)
            {
                writer.WriteStartObject("features");
                foreach (var feature in definition.Features.OrderBy(
                             static item => item.Reference,
                             StringComparer.Ordinal))
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    writer.WriteStartObject(feature.Reference);
                    foreach (var option in feature.Options)
                    {
                        writer.WriteString(option.Key, option.Value);
                    }

                    writer.WriteEndObject();
                }

                writer.WriteEndObject();
            }

            if (!definition.ForwardedPorts.IsEmpty)
            {
                writer.WriteStartArray("forwardPorts");
                foreach (var port in definition.ForwardedPorts.OrderBy(
                             static item => item.Port))
                {
                    writer.WriteNumberValue(port.Port);
                }

                writer.WriteEndArray();
                writer.WriteStartObject("portsAttributes");
                foreach (var port in definition.ForwardedPorts.OrderBy(
                             static item => item.Port))
                {
                    writer.WriteStartObject(port.Port.ToString(
                        System.Globalization.CultureInfo.InvariantCulture));
                    writer.WriteString("label", port.Label);
                    writer.WriteEndObject();
                }

                writer.WriteEndObject();
            }

            if (!definition.Mounts.IsEmpty)
            {
                writer.WriteStartArray("mounts");
                foreach (var mount in definition.Mounts.OrderBy(
                             static item => item.Target,
                             StringComparer.Ordinal))
                {
                    writer.WriteStartObject();
                    writer.WriteString(
                        "type",
                        mount.Kind == DevContainerMountKind.Bind ? "bind" : "volume");
                    writer.WriteString("source", mount.Source);
                    writer.WriteString("target", mount.Target);
                    writer.WriteEndObject();
                }

                writer.WriteEndArray();
            }

            if (definition.ContainerUser is not null)
            {
                writer.WriteString("containerUser", definition.ContainerUser);
            }

            if (definition.RemoteUser is not null)
            {
                writer.WriteString("remoteUser", definition.RemoteUser);
            }

            foreach (var command in definition.LifecycleCommands.OrderBy(
                         static item => item.Stage))
            {
                writer.WritePropertyName(StageName(command.Stage));
                if (command.ShellCommand is not null)
                {
                    writer.WriteStringValue(command.ShellCommand);
                }
                else
                {
                    writer.WriteStartArray();
                    foreach (var argument in command.Arguments)
                    {
                        writer.WriteStringValue(argument);
                    }

                    writer.WriteEndArray();
                }
            }

            writer.WriteEndObject();
        });
    }

    private static void RenderProfile(Utf8JsonWriter writer, DevContainerProfile profile)
    {
        switch (profile)
        {
            case DevContainerImageProfile image:
                writer.WriteString("image", image.Image);
                break;
            case DevContainerDockerfileProfile dockerfile:
                writer.WriteStartObject("build");
                writer.WriteString("dockerfile", "Dockerfile");
                writer.WriteString("context", dockerfile.BuildContext);
                writer.WriteEndObject();
                break;
            case DevContainerComposeProfile compose:
                writer.WriteString("dockerComposeFile", "compose.yaml");
                writer.WriteString("service", compose.Service);
                writer.WriteString("workspaceFolder", compose.WorkspaceFolder);
                writer.WriteString("shutdownAction", "stopCompose");
                break;
        }
    }

    private static string RenderCompose(DevContainerComposeProfile profile)
    {
        var builder = new StringBuilder();
        builder.AppendLine("services:");
        builder.Append("  ").Append(profile.Service).AppendLine(":");
        if (profile.Image is not null)
        {
            builder
                .Append("    image: ")
                .AppendLine(YamlScalar(profile.Image));
        }
        else
        {
            builder.AppendLine("    build:");
            builder
                .Append("      context: ")
                .AppendLine(YamlScalar(profile.BuildContext));
            builder.AppendLine("      dockerfile: '.devcontainer/Dockerfile'");
        }

        builder.AppendLine("    volumes:");
        builder.AppendLine("      - type: bind");
        builder.AppendLine("        source: '..'");
        builder
            .Append("        target: ")
            .AppendLine(YamlScalar(profile.WorkspaceFolder));
        return builder.ToString();
    }

    private static byte[] RenderInputEvidence(DevContainerDefinition definition)
    {
        return WriteJson(writer =>
        {
            writer.WriteStartObject();
            writer.WriteString("identity", definition.Identity.Value);
            writer.WriteString("version", definition.Version.Value);
            writer.WriteString("name", definition.Name);
            writer.WriteString("profile", ProfileName(definition.Profile));
            switch (definition.Profile)
            {
                case DevContainerImageProfile image:
                    writer.WriteString("image", image.Image);
                    break;
                case DevContainerDockerfileProfile dockerfile:
                    WriteArtifactEvidence(writer, "dockerfile", dockerfile.Dockerfile);
                    writer.WriteString("buildContext", dockerfile.BuildContext);
                    break;
                case DevContainerComposeProfile compose:
                    writer.WriteString("service", compose.Service);
                    writer.WriteString("workspaceFolder", compose.WorkspaceFolder);
                    if (compose.Image is not null)
                    {
                        writer.WriteString("image", compose.Image);
                    }
                    else
                    {
                        WriteArtifactEvidence(writer, "dockerfile", compose.Dockerfile!);
                        writer.WriteString("buildContext", compose.BuildContext);
                    }

                    break;
            }

            writer.WriteStartArray("features");
            foreach (var feature in definition.Features.OrderBy(
                         static item => item.Reference,
                         StringComparer.Ordinal))
            {
                writer.WriteStartObject();
                writer.WriteString("reference", feature.Reference);
                writer.WriteString("expectedDigest", feature.ExpectedDigest.Value);
                writer.WriteStartObject("options");
                foreach (var option in feature.Options)
                {
                    writer.WriteString(option.Key, option.Value);
                }

                writer.WriteEndObject();
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteStartArray("mounts");
            foreach (var mount in definition.Mounts.OrderBy(
                         static item => item.Target,
                         StringComparer.Ordinal))
            {
                writer.WriteStartObject();
                writer.WriteString("kind", mount.Kind.ToString());
                writer.WriteString("source", mount.Source);
                writer.WriteString("target", mount.Target);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteStartArray("ports");
            foreach (var port in definition.ForwardedPorts.OrderBy(
                         static item => item.Port))
            {
                writer.WriteStartObject();
                writer.WriteNumber("port", port.Port);
                writer.WriteString("label", port.Label);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteString("containerUser", definition.ContainerUser);
            writer.WriteString("remoteUser", definition.RemoteUser);
            writer.WriteStartArray("lifecycle");
            foreach (var command in definition.LifecycleCommands.OrderBy(
                         static item => item.Stage))
            {
                writer.WriteStartObject();
                writer.WriteString("stage", StageName(command.Stage));
                if (command.ShellCommand is not null)
                {
                    writer.WriteString("shellCommand", command.ShellCommand);
                }
                else
                {
                    writer.WriteStartArray("arguments");
                    foreach (var argument in command.Arguments)
                    {
                        writer.WriteStringValue(argument);
                    }

                    writer.WriteEndArray();
                }

                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteStartArray("scripts");
            foreach (var script in definition.Scripts.OrderBy(
                         static item => item.RelativePath,
                         StringComparer.Ordinal))
            {
                writer.WriteStartObject();
                writer.WriteString("path", script.RelativePath);
                writer.WriteString("digest", script.Digest.Value);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
        });
    }

    private static ImmutableArray<byte> RenderLock(
        DevContainerDefinition definition,
        Sha256Digest inputDigest,
        ImmutableArray<DevContainerGeneratedFile> files)
    {
        return Bytes(WriteJson(writer =>
        {
            writer.WriteStartObject();
            writer.WriteString("profile", "program-kit-dev-container-1.0.0");
            writer.WriteString("definition", definition.Identity.Value);
            writer.WriteString("definitionVersion", definition.Version.Value);
            writer.WriteString("inputSha256", inputDigest.Value);
            writer.WriteStartObject("specification");
            writer.WriteString("repository", "https://github.com/devcontainers/spec");
            writer.WriteString("commit", SpecificationCommit);
            writer.WriteString("baseSchema", BaseSchemaUri);
            writer.WriteString("baseSchemaSha256", BaseSchemaSha256);
            writer.WriteEndObject();
            writer.WriteStartObject("authority");
            writer.WriteString("designSha256", DesignSha256);
            writer.WriteString("planSha256", PlanSha256);
            writer.WriteEndObject();
            writer.WriteStartArray("files");
            foreach (var file in files)
            {
                writer.WriteStartObject();
                writer.WriteString("path", file.RelativePath);
                writer.WriteString("sha256", Digest(file.Content.AsSpan()).Value);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteBoolean("executionPerformed", false);
            writer.WriteBoolean("governedWorkBoundaryClaimed", false);
            writer.WriteString(
                "composeScope",
                definition.Profile is DevContainerComposeProfile
                    ? "single-primary-development-service"
                    : "absent");
            writer.WriteEndObject();
        }));
    }

    private static void WriteArtifactEvidence(
        Utf8JsonWriter writer,
        string propertyName,
        DevContainerOpaqueArtifact artifact)
    {
        writer.WriteStartObject(propertyName);
        writer.WriteString("path", artifact.RelativePath);
        writer.WriteString("digest", artifact.Digest.Value);
        writer.WriteBoolean("attestedSecretFree", artifact.AttestedSecretFree);
        writer.WriteEndObject();
    }

    private static byte[] WriteJson(Action<Utf8JsonWriter> write)
    {
        using MemoryStream stream = new();
        using (Utf8JsonWriter writer = new(stream, new JsonWriterOptions { Indented = true }))
        {
            write(writer);
        }

        stream.WriteByte((byte)'\n');
        return stream.ToArray();
    }

    private static void AddOpaque(
        ImmutableArray<DevContainerGeneratedFile>.Builder files,
        DevContainerOpaqueArtifact artifact) =>
        files.Add(new DevContainerGeneratedFile(
            artifact.RelativePath.Replace('\\', '/'),
            artifact.Content));

    private static void EnsureUniquePaths(ImmutableArray<DevContainerGeneratedFile> files)
    {
        var paths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var file in files)
        {
            if (!paths.Add(file.RelativePath))
            {
                throw new DevContainerGenerationException(
                    DevContainerDiagnosticIds.UnsafePath,
                    "/outputs",
                    "Generated output paths must be unique.");
            }
        }
    }

    private static Sha256Digest TreeDigest(ImmutableArray<DevContainerGeneratedFile> files)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var file in files)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(file.RelativePath));
            hash.AppendData([0]);
            hash.AppendData(SHA256.HashData(file.Content.AsSpan()));
            hash.AppendData([0]);
        }

        return new Sha256Digest(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(hash.GetHashAndReset())));
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(content))));

    private static ImmutableArray<byte> Bytes(byte[] content) =>
        ImmutableArray.Create(content);

    private static ImmutableArray<byte> Bytes(string content) =>
        Bytes(Encoding.UTF8.GetBytes(content));

    private static string StageName(DevContainerLifecycleStage stage) =>
        stage switch
        {
            DevContainerLifecycleStage.Initialize => "initializeCommand",
            DevContainerLifecycleStage.OnCreate => "onCreateCommand",
            DevContainerLifecycleStage.UpdateContent => "updateContentCommand",
            DevContainerLifecycleStage.PostCreate => "postCreateCommand",
            DevContainerLifecycleStage.PostStart => "postStartCommand",
            DevContainerLifecycleStage.PostAttach => "postAttachCommand",
            _ => throw new DevContainerGenerationException(
                DevContainerDiagnosticIds.InvalidComposition,
                "/lifecycleCommands/stage",
                "The lifecycle stage is unsupported."),
        };

    private static string ProfileName(DevContainerProfile profile) =>
        profile switch
        {
            DevContainerImageProfile => "image",
            DevContainerDockerfileProfile => "dockerfile",
            DevContainerComposeProfile => "compose",
            _ => "unsupported",
        };

    private static string YamlScalar(string value) =>
        string.Concat("'", value.Replace("'", "''", StringComparison.Ordinal), "'");
}
