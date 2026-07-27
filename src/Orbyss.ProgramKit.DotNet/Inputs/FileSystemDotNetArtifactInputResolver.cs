using System.Security.Cryptography;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Validation;

namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Filesystem resolver with exact allow-list, containment, and digest checks.</summary>
public sealed class FileSystemDotNetArtifactInputResolver : IDotNetArtifactInputResolver
{
    /// <inheritdoc />
    public async ValueTask<ResolvedDotNetArtifactInput> ResolveAsync(
        string readRoot,
        DotNetArtifactInputManifest manifest,
        ArtifactReference revision,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(readRoot);
        ArgumentNullException.ThrowIfNull(manifest);
        ArgumentNullException.ThrowIfNull(revision);

        var matches = manifest.Inputs.IsDefault
            ? []
            : manifest.Inputs
                .Where(entry => DotNetContractKeys.Exact(entry.Revision) ==
                                DotNetContractKeys.Exact(revision))
                .ToArray();
        if (matches.Length != 1)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "The requested exact revision must occur exactly once in the input manifest.",
                "/inputs");
        }

        var relativePath = DotNetPathPolicy.NormalizeRelative(matches[0].RelativePath);
        var canonicalRoot = Path.GetFullPath(readRoot);
        var candidate = Path.GetFullPath(
            Path.Combine(canonicalRoot, relativePath.Replace('/', Path.DirectorySeparatorChar)));
        var rootPrefix = canonicalRoot.TrimEnd(
            Path.DirectorySeparatorChar,
            Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!candidate.StartsWith(rootPrefix, StringComparison.OrdinalIgnoreCase))
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "The manifest path escapes the explicit read root.",
                "/inputs/relativePath");
        }

        byte[] bytes;
        try
        {
            bytes = await File.ReadAllBytesAsync(candidate, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception) when (
            exception is IOException or UnauthorizedAccessException)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "The manifest-listed artifact input could not be read.",
                "/inputs/relativePath",
                exception);
        }

        var actual = Convert.ToHexStringLower(SHA256.HashData(bytes));
        var expected = revision.Digest.Value["sha256:".Length..];
        if (!string.Equals(actual, expected, StringComparison.Ordinal))
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidArtifactInput,
                "The manifest-listed input bytes do not match the exact revision digest.",
                "/inputs/revision/digest");
        }

        return new ResolvedDotNetArtifactInput(revision, relativePath, bytes);
    }
}
