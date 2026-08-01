using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public sealed record CandidateEvaluation(
    IReadOnlyList<JsonObject> GateResults,
    IReadOnlyList<JsonObject> ProviderEvidence,
    ArtifactReference EvidenceArtifact,
    string EvidenceDigest,
    bool Passed);

public sealed class CandidateEvaluator
{
    private readonly CandidateArtifactSetBuilder candidates = new();

    public CandidateEvaluation Evaluate(
        CandidateArtifactSet candidate,
        ResolvedFactoryInput resolved,
        ProviderConstructionResult construction,
        ProviderEvaluationResult providerEvaluation)
    {
        candidates.Rehash(candidate);
        ArtifactManifestEntry evidenceEntry = candidate.Artifacts.SingleOrDefault(static item =>
            string.Equals(item.LogicalPath, ".program-kit/provider-evidence.json", StringComparison.Ordinal))
            ?? throw new InvalidOperationException("The sealed candidate has no exact provider-evidence artifact.");
        ArtifactReference evidenceArtifact = new(
            new GovernedIdentity("orbyss.program-kit", "candidate-evidence", candidate.ConstructionIdentity["sha256:".Length..20], "1", evidenceEntry.Digest),
            evidenceEntry.MediaType,
            evidenceEntry.LogicalPath,
            evidenceEntry.Digest,
            evidenceEntry.Ownership);

        ExactSelection profileSelection = resolved.Input.Request.Selections.Single(static item => item.Role == "target-profile");
        GovernedIdentity candidateIdentity = new(
            "orbyss.program-kit",
            "candidate-artifact-set",
            candidate.ConstructionIdentity["sha256:".Length..20],
            "1",
            candidate.SetDigest);
        GovernedIdentity evidenceIdentity = new(
            "orbyss.program-kit",
            "candidate-evaluation",
            candidate.ConstructionIdentity["sha256:".Length..20],
            "1",
            evidenceEntry.Digest);
        EvidenceReference evidence = new(
            evidenceIdentity,
            candidateIdentity,
            profileSelection.Selected,
            evidenceArtifact,
            "current");
        JsonObject evidenceJson = ContractJson.Evidence(evidence);

        List<JsonObject> gates = new();
        AddGate(gates, "exact-resolution", candidateIdentity, resolved.Lock.ClosureDigest == resolved.Input.Request.ExpectedState?.ClosureDigest, evidenceJson);
        AddGate(gates, "candidate-integrity", candidateIdentity, CandidateBytesAreExact(candidate), evidenceJson);
        AddGate(gates, "ownership", candidateIdentity, OwnershipIsComplete(candidate), evidenceJson);
        AddGate(gates, "provider-support", resolved.ConstructionProvider.Manifest.Identity,
            ProviderSupportIsExact(resolved, profileSelection, providerEvaluation), evidenceJson);
        AddGate(gates, "provider-evaluation", resolved.EvaluationProvider.Manifest.Identity,
            construction.Succeeded && providerEvaluation.Succeeded, evidenceJson);
        AddGate(gates, "package-agreement", candidateIdentity, PackageAgreementIsExact(candidate), evidenceJson);
        AddGate(gates, "claim-class", candidateIdentity, ClaimClassesAreHonest(candidate), evidenceJson);

        bool passed = gates.All(static gate => string.Equals(gate["status"]?.GetValue<string>(), "passed", StringComparison.Ordinal));
        string digest = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(string.Join('\n',
            gates.Select(CanonicalJson.Digest)
                .Concat(construction.Evidence.Select(CanonicalJson.Digest))
                .Concat(providerEvaluation.Evidence.Select(CanonicalJson.Digest))
                .OrderBy(static value => value, StringComparer.Ordinal))));
        return new CandidateEvaluation(
            gates,
            construction.Evidence.Concat(providerEvaluation.Evidence).Select(static item => (JsonObject)item.DeepClone()).ToArray(),
            evidenceArtifact,
            digest,
            passed);
    }

    private static void AddGate(List<JsonObject> gates, string name, GovernedIdentity subject, bool passed, JsonObject evidence)
    {
        GovernedIdentity gate = ContractJson.StableIdentity("orbyss.program-kit", "gate", name, "1.0.0", name);
        gates.Add(ContractJson.Gate(
            gate,
            name == "provider-support" || name == "provider-evaluation" ? "evidence-backed" : "executable-invariant",
            passed ? "passed" : "failed",
            new[] { ContractJson.Subject("governed-identity", subject) },
            new[] { evidence },
            passed ? Array.Empty<string>() : new[] { Contracts.Diagnostics.DiagnosticIds.GateFailed }));
    }

    private static bool CandidateBytesAreExact(CandidateArtifactSet candidate) => candidate.Artifacts.All(artifact =>
    {
        string path = LogicalPaths.ResolveInside(candidate.CandidateRoot, artifact.LogicalPath);
        return File.Exists(path)
            && (File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0
            && string.Equals(Digests.Sha256(File.ReadAllBytes(path)), artifact.Digest, StringComparison.Ordinal);
    });

    private static bool OwnershipIsComplete(CandidateArtifactSet candidate)
    {
        string[] logical = candidate.Artifacts.Select(static artifact => LogicalPaths.Normalize(artifact.LogicalPath)).ToArray();
        return logical.Length == logical.Distinct(StringComparer.Ordinal).Count()
            && logical.Length == logical.Distinct(StringComparer.OrdinalIgnoreCase).Count()
            && candidate.Artifacts.All(static artifact => !string.IsNullOrWhiteSpace(artifact.ProducerIdentity));
    }

    private static bool ProviderSupportIsExact(ResolvedFactoryInput resolved, ExactSelection profile, ProviderEvaluationResult evaluation)
    {
        if (!evaluation.Succeeded
            || resolved.ConstructionProvider.Manifest.Identity != resolved.EvaluationProvider.Manifest.Identity
            || resolved.ConstructionProvider.Manifest.Distribution != resolved.EvaluationProvider.Manifest.Distribution
            || !resolved.ConstructionProvider.Manifest.Profiles.Contains(profile.Selected.Name, StringComparer.Ordinal)
            || !resolved.EvaluationProvider.Manifest.Profiles.Contains(profile.Selected.Name, StringComparer.Ordinal))
        {
            return false;
        }

        return evaluation.Evidence.Any(item =>
            string.Equals(item["providerDigest"]?.GetValue<string>(), resolved.EvaluationProvider.Manifest.Identity.Digest, StringComparison.Ordinal)
            && string.Equals(item["distributionDigest"]?.GetValue<string>(), resolved.EvaluationProvider.Manifest.Distribution.Digest, StringComparison.Ordinal)
            && string.Equals(item["profile"]?.GetValue<string>(), profile.Selected.Name, StringComparison.Ordinal)
            && string.Equals(item["support"]?.GetValue<string>(), "supported", StringComparison.Ordinal));
    }

    private static bool PackageAgreementIsExact(CandidateArtifactSet candidate)
    {
        ArtifactManifestEntry[] packages = candidate.Artifacts.Where(static item =>
            item.LogicalPath.StartsWith("feeds/component/", StringComparison.Ordinal)
            && item.LogicalPath.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase)).ToArray();
        ArtifactManifestEntry[] bindings = candidate.Artifacts.Where(static item => item.LogicalPath.EndsWith("program-kit.package-binding.json", StringComparison.Ordinal)).ToArray();
        if (packages.Length != 1 || bindings.Length != 1)
        {
            return false;
        }

        JsonObject binding = CanonicalJson.Parse(File.ReadAllBytes(LogicalPaths.ResolveInside(candidate.CandidateRoot, bindings[0].LogicalPath))) as JsonObject
            ?? throw new InvalidDataException("The package binding must be a JSON object.");
        byte[] packageBytes = File.ReadAllBytes(LogicalPaths.ResolveInside(candidate.CandidateRoot, packages[0].LogicalPath));
        string contentHash = Convert.ToBase64String(System.Security.Cryptography.SHA512.HashData(packageBytes));
        return string.Equals(binding["digest"]?.GetValue<string>(), packages[0].Digest, StringComparison.Ordinal)
            && string.Equals(binding["nugetContentHash"]?.GetValue<string>(), contentHash, StringComparison.Ordinal)
            && string.Equals(binding["producerConstructionIdentity"]?.GetValue<string>(), candidate.ConstructionIdentity, StringComparison.Ordinal);
    }

    private static bool ClaimClassesAreHonest(CandidateArtifactSet candidate) => candidate.Artifacts.All(static artifact =>
        artifact.LogicalPath.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase)
            || artifact.LogicalPath.EndsWith("packages.lock.json", StringComparison.Ordinal)
            || artifact.LogicalPath.EndsWith("program-kit.package-binding.json", StringComparison.Ordinal)
            || string.Equals(artifact.LogicalPath, ".program-kit/provider-evidence.json", StringComparison.Ordinal)
            || string.Equals(artifact.LogicalPath, ".program-kit/artifact-manifest.json", StringComparison.Ordinal)
            ? artifact.ClaimClass == ClaimClass.VerifiedEquivalent
            : artifact.Ownership is ArtifactOwnership.ConsumerOwned or ArtifactOwnership.SeededHandoff
                ? artifact.ClaimClass == ClaimClass.CustomBounded
                : artifact.ClaimClass == ClaimClass.CanonicalByte);
}
