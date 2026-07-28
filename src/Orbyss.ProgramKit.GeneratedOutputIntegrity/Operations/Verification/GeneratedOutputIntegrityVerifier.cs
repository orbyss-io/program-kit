using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Serialization;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

/// <summary>Offline verifier for one complete Program Kit-generated host root.</summary>
public sealed class GeneratedOutputIntegrityVerifier :
    IGeneratedOutputIntegrityVerifier
{
    private const long MaximumIntegrityArtifactLength = 16 * 1024 * 1024;
    private const int MaximumManifestEntries = 100_000;
    private static readonly SearchValues<char> LowerHex =
        SearchValues.Create("0123456789abcdef");

    /// <summary>Recomputes current bytes and reports every observable drift item.</summary>
    public async ValueTask<GeneratedOutputIntegrityResult> VerifyAsync(
        string rootPath,
        CancellationToken cancellationToken)
    {
        var root = GeneratedOutputPathPolicy.RequireAbsoluteRoot(rootPath);
        var issues = ImmutableArray.CreateBuilder<GeneratedOutputIntegrityIssue>();
        if (!Directory.Exists(root))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsealed,
                root,
                "the declared generated root is missing."));
            return Result(issues);
        }

        if (IsReparsePoint(root))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsafe,
                root,
                "the generated root is a link or reparse point."));
            return Result(issues);
        }

        var anchorPath = GeneratedOutputPathPolicy.AnchorPath(root);
        if (!File.Exists(anchorPath))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsealed,
                anchorPath,
                "the sibling external anchor is missing."));
            return Result(issues);
        }

        if (IsReparsePoint(anchorPath))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsafe,
                anchorPath,
                "the sibling external anchor is a link or reparse point."));
            return Result(issues);
        }

        GeneratedOutputAnchor anchor;
        ReadOnlyMemory<byte> anchorBytes;
        try
        {
            anchorBytes = await ReadBoundedAsync(
                anchorPath,
                cancellationToken).ConfigureAwait(false);
            anchor = GeneratedOutputIntegritySerializer.ReadAnchor(
                anchorBytes.Span);
            ValidateAnchor(anchor);
        }
        catch (Exception exception) when (
            exception is IOException or
            UnauthorizedAccessException or
            JsonException or
            InvalidDataException)
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Malformed,
                anchorPath,
                "the sibling external anchor is malformed or unreadable."));
            return Result(issues);
        }

        var manifestPath = GeneratedOutputPathPolicy.ResolveUnderRoot(
            root,
            anchor.ManifestPath,
            allowManifest: true);
        if (!File.Exists(manifestPath))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsealed,
                anchor.ManifestPath,
                "the recorded in-tree manifest is missing."));
            return Result(issues);
        }

        if (IsReparsePoint(manifestPath))
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unsafe,
                anchor.ManifestPath,
                "the in-tree manifest is a link or reparse point."));
            return Result(issues);
        }

        GeneratedOutputManifest manifest;
        try
        {
            var manifestBytes = await ReadBoundedAsync(
                manifestPath,
                cancellationToken).ConfigureAwait(false);
            var manifestDigest = GeneratedOutputSealer.Digest(
                manifestBytes.Span);
            if (!string.Equals(
                    manifestDigest,
                    anchor.ManifestSha256,
                    StringComparison.Ordinal))
            {
                issues.Add(Issue(
                    GeneratedOutputIntegrityIssueKind.Unsealed,
                    anchor.ManifestPath,
                    "the in-tree manifest bytes do not match the external anchor."));
                return Result(issues);
            }

            manifest = GeneratedOutputIntegritySerializer.ReadManifest(
                manifestBytes.Span);
            ValidateManifest(manifest);
        }
        catch (Exception exception) when (
            exception is IOException or
            UnauthorizedAccessException or
            JsonException or
            InvalidDataException)
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Malformed,
                anchor.ManifestPath,
                "the in-tree manifest is malformed or unreadable."));
            return Result(issues);
        }

        var expected = new Dictionary<string, GeneratedOutputManifestEntry>(
            StringComparer.Ordinal);
        foreach (var entry in manifest.Files)
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                GeneratedOutputPathPolicy.RequireNormalizedRelativePath(
                    entry.Path);
                ValidateEntry(entry);
                if (!expected.TryAdd(entry.Path, entry))
                {
                    throw new InvalidDataException(
                        "Manifest payload paths must be unique.");
                }
            }
            catch (InvalidDataException)
            {
                issues.Add(Issue(
                    GeneratedOutputIntegrityIssueKind.Malformed,
                    entry.Path,
                    "the manifest contains an unsafe or invalid payload entry."));
            }
        }

        if (issues.Count > 0)
        {
            return Result(issues);
        }

        var actual = EnumerateFiles(root, issues, cancellationToken);
        foreach (var entry in expected.Values)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!actual.Remove(entry.Path, out var currentPath))
            {
                issues.Add(Issue(
                    GeneratedOutputIntegrityIssueKind.Missing,
                    entry.Path,
                    "a recorded generated file is missing."));
                continue;
            }

            try
            {
                var info = new FileInfo(currentPath);
                if (info.Length != entry.Length)
                {
                    issues.Add(Issue(
                        GeneratedOutputIntegrityIssueKind.Modified,
                        entry.Path,
                        "a recorded generated file has a different length."));
                    continue;
                }

                await using var stream = new FileStream(
                    currentPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.Read,
                    bufferSize: 81920,
                    FileOptions.Asynchronous | FileOptions.SequentialScan);
                var digest = string.Concat(
                    "sha256:",
                    Convert.ToHexStringLower(
                        await SHA256.HashDataAsync(
                            stream,
                            cancellationToken).ConfigureAwait(false)));
                if (!string.Equals(
                        digest,
                        entry.Sha256,
                        StringComparison.Ordinal))
                {
                    issues.Add(Issue(
                        GeneratedOutputIntegrityIssueKind.Modified,
                        entry.Path,
                        "a recorded generated file has different bytes."));
                }
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException)
            {
                issues.Add(Issue(
                    GeneratedOutputIntegrityIssueKind.Unsafe,
                    entry.Path,
                    "a recorded generated file could not be read safely."));
            }
        }

        actual.Remove(
            GeneratedOutputIntegrityConstants.ManifestRelativePath);
        foreach (var unexpected in actual.Keys)
        {
            issues.Add(Issue(
                GeneratedOutputIntegrityIssueKind.Unexpected,
                unexpected,
                "an unrecorded file exists under the generated root."));
        }

        return Result(issues);
    }

    private static Dictionary<string, string> EnumerateFiles(
        string root,
        ImmutableArray<GeneratedOutputIntegrityIssue>.Builder issues,
        CancellationToken cancellationToken)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        var pending = new Stack<string>();
        pending.Push(root);
        while (pending.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var directory = pending.Pop();
            IEnumerable<string> entries;
            try
            {
                entries = Directory.EnumerateFileSystemEntries(directory)
                    .Order(StringComparer.Ordinal)
                    .ToArray();
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException)
            {
                issues.Add(Issue(
                    GeneratedOutputIntegrityIssueKind.Unsafe,
                    Relative(root, directory),
                    "a generated directory could not be enumerated safely."));
                continue;
            }

            foreach (var entry in entries)
            {
                cancellationToken.ThrowIfCancellationRequested();
                var relative = Relative(root, entry);
                FileAttributes attributes;
                try
                {
                    attributes = File.GetAttributes(entry);
                }
                catch (Exception exception) when (
                    exception is IOException or UnauthorizedAccessException)
                {
                    issues.Add(Issue(
                        GeneratedOutputIntegrityIssueKind.Unsafe,
                        relative,
                        "a generated path could not be inspected safely."));
                    continue;
                }

                if ((attributes & FileAttributes.ReparsePoint) != 0)
                {
                    issues.Add(Issue(
                        GeneratedOutputIntegrityIssueKind.Unsafe,
                        relative,
                        "a link or reparse point exists under the generated root."));
                    continue;
                }

                if ((attributes & FileAttributes.Directory) != 0)
                {
                    pending.Push(entry);
                }
                else if (!result.TryAdd(relative, entry))
                {
                    issues.Add(Issue(
                        GeneratedOutputIntegrityIssueKind.Unsafe,
                        relative,
                        "two filesystem entries resolve to the same normalized path."));
                }
            }
        }

        return result;
    }

    private static async ValueTask<ReadOnlyMemory<byte>> ReadBoundedAsync(
        string path,
        CancellationToken cancellationToken)
    {
        var length = new FileInfo(path).Length;
        if (length is < 1 or > MaximumIntegrityArtifactLength)
        {
            throw new InvalidDataException(
                "An integrity artifact has an invalid length.");
        }

        return await File.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
    }

    private static void ValidateAnchor(GeneratedOutputAnchor anchor)
    {
        if (anchor.Schema != GeneratedOutputIntegrityConstants.AnchorSchema ||
            anchor.FormatVersion != GeneratedOutputIntegrityConstants.FormatVersion ||
            anchor.ManifestPath != GeneratedOutputIntegrityConstants.ManifestRelativePath ||
            !IsDigest(anchor.ManifestSha256))
        {
            throw new InvalidDataException(
                "The generated-output anchor contract is invalid.");
        }
    }

    private static void ValidateManifest(GeneratedOutputManifest manifest)
    {
        if (manifest.Schema != GeneratedOutputIntegrityConstants.ManifestSchema ||
            manifest.FormatVersion != GeneratedOutputIntegrityConstants.FormatVersion ||
            manifest.Ownership != GeneratedOutputIntegrityConstants.Ownership ||
            manifest.Files.IsDefaultOrEmpty ||
            manifest.Files.Length > MaximumManifestEntries)
        {
            throw new InvalidDataException(
                "The generated-output manifest contract is invalid.");
        }

        string? previous = null;
        foreach (var entry in manifest.Files)
        {
            if (previous is not null &&
                string.CompareOrdinal(previous, entry.Path) >= 0)
            {
                throw new InvalidDataException(
                    "Manifest entries must be unique and ordinally ordered.");
            }

            previous = entry.Path;
        }
    }

    private static void ValidateEntry(GeneratedOutputManifestEntry entry)
    {
        if (!IsDigest(entry.Sha256) || entry.Length < 0)
        {
            throw new InvalidDataException(
                "A generated-output manifest entry is invalid.");
        }
    }

    private static bool IsDigest(string value) =>
        value.Length == 71 &&
        value.StartsWith("sha256:", StringComparison.Ordinal) &&
        value.AsSpan(7).IndexOfAnyExcept(LowerHex) < 0;

    private static bool IsReparsePoint(string path)
    {
        var attributes = File.GetAttributes(path);
        return (attributes & FileAttributes.ReparsePoint) != 0;
    }

    private static string Relative(string root, string path) =>
        string.Equals(root, path, GeneratedOutputPathPolicy.PathComparison)
            ? "."
            : Path.GetRelativePath(root, path).Replace('\\', '/');

    private static GeneratedOutputIntegrityIssue Issue(
        GeneratedOutputIntegrityIssueKind kind,
        string path,
        string detail) =>
        new(
            kind,
            path,
            string.Concat(
                "Tampered-with Program Kit generated output: ",
                detail));

    private static GeneratedOutputIntegrityResult Result(
        ImmutableArray<GeneratedOutputIntegrityIssue>.Builder issues) =>
        new(
            issues
                .OrderBy(static issue => issue.Path, StringComparer.Ordinal)
                .ThenBy(static issue => issue.Kind)
                .ToImmutableArray());
}
