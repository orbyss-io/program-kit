using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;
using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;
using Orbyss.ProgramKit.DevContainers.Contracts.Diagnostics;
using Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;
using Orbyss.ProgramKit.DevContainers.Contracts.Mounts;
using Orbyss.ProgramKit.DevContainers.Contracts.Profiles;

namespace Orbyss.ProgramKit.DevContainers.Operations.Validation;

/// <summary>Fail-closed semantic validator for the bounded Dev Container profile.</summary>
public sealed partial class DevContainerDefinitionValidator :
    IDevContainerDefinitionValidator
{
    private const int MaximumOpaqueBytes = 1_048_576;
    private static readonly string[] SecretMarkers =
    [
        "authorization: bearer ",
        "begin private key",
        "client_secret=",
        "client-secret=",
        "password=",
        "api_key=",
        "api-key=",
        "access_token=",
        "access-token=",
    ];

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DevContainerDefinition value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();

        if (string.IsNullOrWhiteSpace(value.Name) || value.Name.Length > 128)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidComposition,
                "The display name must contain between 1 and 128 characters.",
                "/name");
        }

        ValidateProfile(value.Profile, diagnostics);
        ValidateFeatures(value, diagnostics);
        ValidateMounts(value, diagnostics);
        ValidatePorts(value, diagnostics);
        ValidateUser(value.ContainerUser, "/containerUser", diagnostics);
        ValidateUser(value.RemoteUser, "/remoteUser", diagnostics);
        ValidateLifecycle(value, diagnostics);
        ValidateScripts(value, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateProfile(
        DevContainerProfile? profile,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        switch (profile)
        {
            case DevContainerImageProfile image:
                ValidateImage(image.Image, "/profile/image", diagnostics);
                break;
            case DevContainerDockerfileProfile dockerfile:
                ValidateDockerfile(
                    dockerfile.Dockerfile,
                    dockerfile.BuildContext,
                    "/profile",
                    diagnostics);
                break;
            case DevContainerComposeProfile compose:
                if (!ServiceName().IsMatch(compose.Service))
                {
                    Add(
                        diagnostics,
                        DevContainerDiagnosticIds.InvalidProfile,
                        "The Compose service name is invalid.",
                        "/profile/service");
                }

                if (!AbsoluteContainerPath().IsMatch(compose.WorkspaceFolder))
                {
                    Add(
                        diagnostics,
                        DevContainerDiagnosticIds.UnsafePath,
                        "The Compose workspace folder must be an absolute normalized container path.",
                        "/profile/workspaceFolder");
                }

                if ((compose.Image is null) == (compose.Dockerfile is null))
                {
                    Add(
                        diagnostics,
                        DevContainerDiagnosticIds.InvalidProfile,
                        "A Compose profile requires exactly one image or Dockerfile.",
                        "/profile");
                }
                else if (compose.Image is not null)
                {
                    ValidateImage(compose.Image, "/profile/image", diagnostics);
                }
                else
                {
                    ValidateDockerfile(
                        compose.Dockerfile!,
                        compose.BuildContext,
                        "/profile",
                        diagnostics);
                }

                break;
            default:
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidProfile,
                    "The Dev Container construction profile is required and must be supported.",
                    "/profile");
                break;
        }
    }

    private static void ValidateDockerfile(
        DevContainerOpaqueArtifact artifact,
        string context,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!string.Equals(
                artifact.RelativePath,
                ".devcontainer/Dockerfile",
                StringComparison.Ordinal))
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafePath,
                "The generated Dockerfile path must be exactly .devcontainer/Dockerfile.",
                string.Concat(path, "/dockerfile/relativePath"));
        }

        if (!string.Equals(context, "..", StringComparison.Ordinal))
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafePath,
                "The bounded Dockerfile profile uses the explicit workspace-root context '..'.",
                string.Concat(path, "/buildContext"));
        }

        ValidateOpaque(artifact, string.Concat(path, "/dockerfile"), diagnostics);
    }

    private static void ValidateImage(
        string? image,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (image is null || !PinnedImage().IsMatch(image))
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidProfile,
                "The image must be a lowercase OCI reference pinned by a SHA-256 digest.",
                path);
        }
    }

    private static void ValidateFeatures(
        DevContainerDefinition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Features.IsDefault)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidFeature,
                "The feature collection must be initialized.",
                "/features");
            return;
        }

        var references = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Features.Length; index++)
        {
            var feature = value.Features[index];
            var path = string.Concat("/features/", index);
            if (feature is null || !ExactFeature().IsMatch(feature.Reference))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidFeature,
                    "A feature reference must use a lowercase registry path and exact three-part version.",
                    string.Concat(path, "/reference"));
                continue;
            }

            if (!references.Add(feature.Reference))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidFeature,
                    "Feature references must be unique.",
                    string.Concat(path, "/reference"));
            }

            if (feature.Options is null)
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidFeature,
                    "Feature options must be initialized.",
                    string.Concat(path, "/options"));
                continue;
            }

            foreach (var option in feature.Options)
            {
                if (!OptionName().IsMatch(option.Key) || IsSensitiveName(option.Key) ||
                    ContainsSecretMarker(option.Value))
                {
                    Add(
                        diagnostics,
                        DevContainerDiagnosticIds.InvalidFeature,
                        "Feature options must be structurally safe and must not carry secret material.",
                        string.Concat(path, "/options/", option.Key));
                }
            }
        }
    }

    private static void ValidateMounts(
        DevContainerDefinition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Mounts.IsDefault)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidComposition,
                "The mount collection must be initialized.",
                "/mounts");
            return;
        }

        var targets = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Mounts.Length; index++)
        {
            var mount = value.Mounts[index];
            var path = string.Concat("/mounts/", index);
            if (mount is null || !AbsoluteContainerPath().IsMatch(mount.Target) ||
                !targets.Add(mount.Target))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidComposition,
                    "Mount targets must be unique absolute normalized container paths.",
                    string.Concat(path, "/target"));
                continue;
            }

            var validSource = mount.Kind switch
            {
                DevContainerMountKind.Bind =>
                    mount.Source is not null && WorkspaceSource().IsMatch(mount.Source),
                DevContainerMountKind.Volume =>
                    mount.Source is not null && VolumeName().IsMatch(mount.Source),
                _ => false,
            };
            if (!validSource)
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.UnsafePath,
                    "Mount sources must be explicit workspace-rooted bind paths or safe named volumes.",
                    string.Concat(path, "/source"));
            }
        }
    }

    private static void ValidatePorts(
        DevContainerDefinition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.ForwardedPorts.IsDefault)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidComposition,
                "The forwarded-port collection must be initialized.",
                "/forwardedPorts");
            return;
        }

        var ports = new HashSet<int>();
        for (var index = 0; index < value.ForwardedPorts.Length; index++)
        {
            var port = value.ForwardedPorts[index];
            if (port is null || port.Port is < 1 or > 65535 || !ports.Add(port.Port) ||
                string.IsNullOrWhiteSpace(port.Label) || ContainsSecretMarker(port.Label))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidComposition,
                    "Forwarded ports must be unique, valid, and carry a non-sensitive label.",
                    string.Concat("/forwardedPorts/", index));
            }
        }
    }

    private static void ValidateUser(
        string? user,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (user is null)
        {
            return;
        }

        if (!UserName().IsMatch(user) ||
            string.Equals(user, "root", StringComparison.Ordinal) ||
            string.Equals(user, "0", StringComparison.Ordinal))
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidComposition,
                "An explicit user must be a safe non-root POSIX user name.",
                path);
        }
    }

    private static void ValidateLifecycle(
        DevContainerDefinition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.LifecycleCommands.IsDefault)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.InvalidComposition,
                "The lifecycle-command collection must be initialized.",
                "/lifecycleCommands");
            return;
        }

        var stages = new HashSet<DevContainerLifecycleStage>();
        for (var index = 0; index < value.LifecycleCommands.Length; index++)
        {
            var command = value.LifecycleCommands[index];
            var path = string.Concat("/lifecycleCommands/", index);
            if (command is null || !stages.Add(command.Stage))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidComposition,
                    "Lifecycle stages must be unique and supported.",
                    string.Concat(path, "/stage"));
                continue;
            }

            var hasShell = command.ShellCommand is not null;
            var hasArguments = !command.Arguments.IsDefaultOrEmpty;
            if (hasShell == hasArguments ||
                hasShell && (string.IsNullOrWhiteSpace(command.ShellCommand) ||
                             ContainsSecretMarker(command.ShellCommand!)) ||
                hasArguments && command.Arguments.Any(static argument =>
                    string.IsNullOrEmpty(argument) || ContainsSecretMarker(argument)))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidComposition,
                    "A lifecycle command requires exactly one non-secret shell string or exec array.",
                    path);
            }
        }
    }

    private static void ValidateScripts(
        DevContainerDefinition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Scripts.IsDefault)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafeOpaqueContent,
                "The script collection must be initialized.",
                "/scripts");
            return;
        }

        var paths = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Scripts.Length; index++)
        {
            var script = value.Scripts[index];
            var path = string.Concat("/scripts/", index);
            if (script is null || !ScriptPath().IsMatch(script.RelativePath) ||
                !paths.Add(script.RelativePath))
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.UnsafePath,
                    "Script paths must be unique normalized files under .devcontainer/scripts.",
                    string.Concat(path, "/relativePath"));
                continue;
            }

            ValidateOpaque(script, path, diagnostics);
            var referenced = value.LifecycleCommands.Any(command =>
                command is not null &&
                (command.ShellCommand?.Contains(script.RelativePath, StringComparison.Ordinal) == true ||
                 command.Arguments.Any(argument =>
                     string.Equals(argument, script.RelativePath, StringComparison.Ordinal))));
            if (!referenced)
            {
                Add(
                    diagnostics,
                    DevContainerDiagnosticIds.InvalidComposition,
                    "Every generated script must be referenced by an explicit lifecycle command.",
                    path);
            }
        }
    }

    private static void ValidateOpaque(
        DevContainerOpaqueArtifact artifact,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!artifact.AttestedSecretFree || artifact.Content.IsDefaultOrEmpty ||
            artifact.Content.Length > MaximumOpaqueBytes)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafeOpaqueContent,
                "Opaque content must be non-empty, bounded, and explicitly attested secret-free.",
                path);
            return;
        }

        var actual = new Sha256Digest(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(artifact.Content.AsSpan()))));
        if (actual != artifact.Digest)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafeOpaqueContent,
                "Opaque content bytes do not match the exact supplied digest.",
                string.Concat(path, "/digest"));
        }

        string text;
        try
        {
            var strictUtf8 = new UTF8Encoding(false, true);
            text = strictUtf8.GetString(artifact.Content.AsSpan());
        }
        catch (DecoderFallbackException)
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafeOpaqueContent,
                "Opaque content must be valid UTF-8 text.",
                string.Concat(path, "/content"));
            return;
        }

        if (text.Contains('\0') || ContainsSecretMarker(text))
        {
            Add(
                diagnostics,
                DevContainerDiagnosticIds.UnsafeOpaqueContent,
                "Opaque content contains forbidden binary or apparent secret material.",
                string.Concat(path, "/content"));
        }
    }

    private static bool IsSensitiveName(string name) =>
        name.Contains("secret", StringComparison.OrdinalIgnoreCase) ||
        name.Contains("password", StringComparison.OrdinalIgnoreCase) ||
        name.Contains("token", StringComparison.OrdinalIgnoreCase) ||
        name.Contains("credential", StringComparison.OrdinalIgnoreCase) ||
        name.Contains("apikey", StringComparison.OrdinalIgnoreCase) ||
        name.Contains("api_key", StringComparison.OrdinalIgnoreCase);

    private static bool ContainsSecretMarker(string value) =>
        SecretMarkers.Any(marker =>
            value.Contains(marker, StringComparison.OrdinalIgnoreCase));

    private static void Add(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string message,
        string path) =>
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));

    [GeneratedRegex("^[a-z0-9][a-z0-9._/-]*(?::[a-z0-9._-]+)?@sha256:[a-f0-9]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex PinnedImage();

    [GeneratedRegex("^[a-z0-9.-]+(?:/[a-z0-9._-]+)+:[0-9]+\\.[0-9]+\\.[0-9]+$", RegexOptions.CultureInvariant)]
    private static partial Regex ExactFeature();

    [GeneratedRegex("^[A-Za-z][A-Za-z0-9_-]{0,63}$", RegexOptions.CultureInvariant)]
    private static partial Regex OptionName();

    [GeneratedRegex("^[a-z0-9][a-z0-9_-]{0,62}$", RegexOptions.CultureInvariant)]
    private static partial Regex ServiceName();

    [GeneratedRegex("^/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$", RegexOptions.CultureInvariant)]
    private static partial Regex AbsoluteContainerPath();

    [GeneratedRegex("^\\$\\{localWorkspaceFolder\\}(?:/[A-Za-z0-9._-]+)*$", RegexOptions.CultureInvariant)]
    private static partial Regex WorkspaceSource();

    [GeneratedRegex("^[a-z0-9][a-z0-9_.-]{0,62}$", RegexOptions.CultureInvariant)]
    private static partial Regex VolumeName();

    [GeneratedRegex("^[a-z_][a-z0-9_-]{0,31}$", RegexOptions.CultureInvariant)]
    private static partial Regex UserName();

    [GeneratedRegex("^\\.devcontainer/scripts/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$", RegexOptions.CultureInvariant)]
    private static partial Regex ScriptPath();
}
