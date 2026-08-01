using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Artifacts;

public sealed class CandidateArtifactSetBuilder
{
    public CandidateArtifactSet Seal(string constructionIdentity, string candidateRoot, IReadOnlyList<ProviderArtifact> declaredArtifacts)
    {
        RejectReparsePoints(candidateRoot);
        ProviderArtifact[] normalizedDeclarations = declaredArtifacts.Select(item => item with
        {
            LogicalPath = LogicalPaths.Normalize(item.LogicalPath),
        }).ToArray();
        string[] declarationCollisions = normalizedDeclarations
            .GroupBy(static item => item.LogicalPath, StringComparer.OrdinalIgnoreCase)
            .Where(static group => group.Count() > 1)
            .Select(static group => group.Key)
            .OrderBy(static item => item, StringComparer.Ordinal)
            .ToArray();
        if (declarationCollisions.Length > 0)
        {
            throw new InvalidOperationException($"Candidate declarations contain duplicate or case-colliding logical paths: {string.Join(", ", declarationCollisions)}");
        }

        Dictionary<string, ProviderArtifact> declared = normalizedDeclarations.ToDictionary(static item => item.LogicalPath, StringComparer.Ordinal);
        HashSet<string> observed = new(StringComparer.Ordinal);
        List<ArtifactManifestEntry> entries = new();
        foreach (string file in Directory.EnumerateFiles(candidateRoot, "*", SearchOption.AllDirectories)
            .OrderBy(static value => value, StringComparer.Ordinal))
        {
            if ((File.GetAttributes(file) & FileAttributes.ReparsePoint) != 0)
            {
                throw new InvalidOperationException("Candidate artifacts cannot be filesystem reparse points.");
            }

            string logicalPath = LogicalPaths.Normalize(Path.GetRelativePath(candidateRoot, file).Replace('\\', '/'));
            if (string.Equals(logicalPath, ".program-kit/artifact-manifest.json", StringComparison.Ordinal))
            {
                continue;
            }

            if (logicalPath.StartsWith(".packages/", StringComparison.Ordinal)
                || logicalPath.Contains("/bin/", StringComparison.Ordinal)
                || logicalPath.Contains("/obj/", StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Transient build output entered the candidate: {logicalPath}");
            }

            if (!declared.TryGetValue(logicalPath, out ProviderArtifact? metadata))
            {
                throw new InvalidOperationException($"The candidate contains an undeclared artifact: {logicalPath}");
            }

            observed.Add(logicalPath);
            entries.Add(new ArtifactManifestEntry(
                logicalPath,
                metadata.Ownership,
                metadata.MediaType,
                Digests.Sha256(File.ReadAllBytes(file)),
                metadata.ProducerIdentity,
                metadata.ClaimClass));
        }

        string[] missingDeclarations = declared.Keys.Except(observed, StringComparer.Ordinal).OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        if (missingDeclarations.Length > 0)
        {
            throw new InvalidOperationException($"Declared candidate artifacts are missing: {string.Join(", ", missingDeclarations)}");
        }

        JsonArray manifestEntries = new(entries.Select(static entry => new JsonObject
        {
            ["logicalPath"] = entry.LogicalPath,
            ["ownership"] = Kebab(entry.Ownership),
            ["mediaType"] = entry.MediaType,
            ["digest"] = entry.Digest,
            ["producer"] = entry.ProducerIdentity,
            ["claimClass"] = Kebab(entry.ClaimClass),
        }).ToArray());
        JsonObject manifest = new()
        {
            ["schema"] = "program-kit.artifact-manifest/v1",
            ["constructionIdentity"] = constructionIdentity,
            ["artifacts"] = manifestEntries,
        };
        string setDigest = CanonicalJson.Digest(manifest);
        manifest["setDigest"] = setDigest;
        string manifestPath = Path.Combine(candidateRoot, ".program-kit", "artifact-manifest.json");
        Directory.CreateDirectory(Path.GetDirectoryName(manifestPath)!);
        File.WriteAllBytes(manifestPath, CanonicalJson.Encode(manifest));
        entries.Add(new ArtifactManifestEntry(
            ".program-kit/artifact-manifest.json",
            ArtifactOwnership.GeneratedOwned,
            "application/json",
            Digests.Sha256(File.ReadAllBytes(manifestPath)),
            "orbyss.program-kit:kernel",
            ClaimClass.VerifiedEquivalent));
        return new CandidateArtifactSet(
            constructionIdentity,
            candidateRoot,
            entries.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray(),
            setDigest,
            CandidateState.Sealed);
    }

    public void Rehash(CandidateArtifactSet candidate)
    {
        RejectReparsePoints(candidate.CandidateRoot);
        foreach (ArtifactManifestEntry artifact in candidate.Artifacts)
        {
            string path = LogicalPaths.ResolveInside(candidate.CandidateRoot, artifact.LogicalPath);
            if (!File.Exists(path)
                || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0
                || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), artifact.Digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Sealed candidate changed: {artifact.LogicalPath}");
            }
        }
    }

    private static void RejectReparsePoints(string root)
    {
        if (!Directory.Exists(root) || (File.GetAttributes(root) & FileAttributes.ReparsePoint) != 0)
        {
            throw new InvalidOperationException("The candidate root is unavailable or is a filesystem reparse point.");
        }

        if (Directory.EnumerateDirectories(root, "*", SearchOption.AllDirectories)
            .Any(static path => (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0))
        {
            throw new InvalidOperationException("Candidate directories cannot be filesystem reparse points.");
        }
    }

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder builder = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(name[index]));
        }

        return builder.ToString();
    }
}
