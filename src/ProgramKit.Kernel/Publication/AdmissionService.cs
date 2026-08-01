using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Evaluation;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Publication;

public sealed record PreparedAdmission(JsonObject ReceiptDocument, ArtifactReference ReceiptReference);

public sealed class AdmissionService
{
    private const string ReceiptSchema = "https://schemas.program-kit.dev/v1/construction-receipt.schema.json";
    private const string SnapshotSchema = "https://schemas.program-kit.dev/v1/workspace-snapshot.schema.json";
    private readonly StructuralSchemaValidator structural = new(new SchemaRegistry());

    public PreparedAdmission Prepare(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        string lockDigest,
        string liveStateDigest,
        CandidateEvaluation evaluation,
        GovernedIdentity profile)
    {
        VerifyAdmissionPreconditions(workspaceRoot, candidate, liveStateDigest, evaluation);
        ArtifactReference journalReference = ReferenceForFile(
            workspaceRoot,
            ".program-kit/publication.journal.json",
            "publication-journal",
            candidate.ConstructionIdentity["sha256:".Length..20]);
        JsonArray receiptArtifacts = new(candidate.Artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(artifact =>
        {
            GovernedIdentity artifactIdentity = new(
                "orbyss.program-kit",
                "generated-artifact",
                artifact.LogicalPath,
                candidate.ConstructionIdentity["sha256:".Length..20],
                artifact.Digest);
            GovernedIdentity producer = ContractJson.StableIdentity(
                "orbyss.program-kit",
                "producer",
                SafeName(artifact.ProducerIdentity),
                "1",
                artifact.ProducerIdentity);
            EvidenceReference verification = new(
                ContractJson.StableIdentity("orbyss.program-kit", "artifact-verification", SafeName(artifact.LogicalPath), "1", $"{artifact.LogicalPath}:{artifact.Digest}:{evaluation.EvidenceDigest}"),
                artifactIdentity,
                profile,
                evaluation.EvidenceArtifact,
                "current");
            return new JsonObject
            {
                ["artifact"] = ContractJson.Artifact(new ArtifactReference(
                    artifactIdentity,
                    artifact.MediaType,
                    artifact.LogicalPath,
                    artifact.Digest,
                    artifact.Ownership)),
                ["producer"] = ContractJson.Identity(producer),
                ["claimClass"] = ContractJson.Kebab(artifact.ClaimClass),
                ["verification"] = ContractJson.Evidence(verification),
            };
        }).ToArray());
        GovernedIdentity retention = ContractJson.StableIdentity("orbyss.program-kit", "retention-policy", "local-workspace", "1.0.0", "local-workspace");
        JsonObject receipt = new()
        {
            ["schema"] = "program-kit.construction-receipt/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["constructionIdentity"] = candidate.ConstructionIdentity,
            ["lockDigest"] = lockDigest,
            ["artifactSetDigest"] = candidate.SetDigest,
            ["artifacts"] = receiptArtifacts,
            ["gateResults"] = new JsonArray(evaluation.GateResults.Select(static gate => gate.DeepClone()).ToArray()),
            ["publicationState"] = "admitted",
            ["observedLiveState"] = liveStateDigest,
            ["publicationJournal"] = ContractJson.Artifact(journalReference),
            ["support"] = new JsonObject
            {
                ["profile"] = ContractJson.Identity(profile),
                ["retentionPolicy"] = ContractJson.Identity(retention),
                ["evidenceFreshness"] = "current",
            },
        };
        System.Collections.Generic.IReadOnlyList<string> receiptFailures = structural.Validate(ReceiptSchema, receipt);
        if (receiptFailures.Count > 0)
        {
            throw new InvalidOperationException($"The prepared admission receipt violates the public receipt contract: {string.Join("; ", receiptFailures)}");
        }

        byte[] bytes = CanonicalJson.Encode(receipt);
        string receiptDigest = Digests.Sha256(bytes);
        ArtifactReference reference = new(
            new GovernedIdentity("orbyss.program-kit", "construction-receipt", candidate.ConstructionIdentity["sha256:".Length..20], "1", receiptDigest),
            "application/json",
            ".program-kit/construction-receipt.json",
            receiptDigest,
            ArtifactOwnership.GeneratedOwned);
        return new PreparedAdmission(receipt, reference);
    }

    public ArtifactReference Admit(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        string liveStateDigest,
        CandidateEvaluation evaluation,
        PreparedAdmission prepared,
        JsonObject snapshot)
    {
        VerifyAdmissionPreconditions(workspaceRoot, candidate, liveStateDigest, evaluation);
        System.Collections.Generic.IReadOnlyList<string> snapshotFailures = structural.Validate(SnapshotSchema, snapshot);
        if (snapshotFailures.Count > 0)
        {
            throw new InvalidOperationException($"The authoritative workspace snapshot violates its public contract: {string.Join("; ", snapshotFailures)}");
        }

        string snapshotPath = Path.Combine(workspaceRoot, ".program-kit", "workspace.snapshot.json");
        RecoverablePublisher.WriteDurable(snapshotPath, CanonicalJson.Encode(snapshot));
        if (!string.Equals(Digests.Sha256(File.ReadAllBytes(snapshotPath)), CanonicalJson.Digest(snapshot), StringComparison.Ordinal))
        {
            throw new InvalidOperationException("The workspace snapshot did not persist exactly.");
        }

        VerifyAdmissionPreconditions(workspaceRoot, candidate, liveStateDigest, evaluation);
        string receiptPath = Path.Combine(workspaceRoot, ".program-kit", "construction-receipt.json");
        if (File.Exists(receiptPath))
        {
            throw new IOException("Admission receipt collision requires an explicitly authorized repair.");
        }

        RecoverablePublisher.WriteDurable(receiptPath, CanonicalJson.Encode(prepared.ReceiptDocument));
        string observed = Digests.Sha256(File.ReadAllBytes(receiptPath));
        if (!string.Equals(observed, prepared.ReceiptReference.Digest, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("The final admission receipt bytes are not exact.");
        }

        return prepared.ReceiptReference;
    }

    private static void VerifyAdmissionPreconditions(
        string workspaceRoot,
        CandidateArtifactSet candidate,
        string liveStateDigest,
        CandidateEvaluation evaluation)
    {
        if (!evaluation.Passed
            || evaluation.GateResults.Count == 0
            || evaluation.GateResults.Any(static gate => gate["status"]?.GetValue<string>() is not "passed"))
        {
            throw new InvalidOperationException("Admission requires complete passed mandatory gate closure.");
        }

        foreach (ArtifactManifestEntry artifact in candidate.Artifacts)
        {
            string path = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            if (!File.Exists(path)
                || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0
                || !string.Equals(Digests.Sha256(File.ReadAllBytes(path)), artifact.Digest, StringComparison.Ordinal))
            {
                throw new InvalidOperationException("Admission requires complete verified live bytes.");
            }
        }

        if (!string.Equals(LiveState.Compute(workspaceRoot, candidate.Artifacts), liveStateDigest, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Admission requires the exact post-publication live state.");
        }

        string journalPath = Path.Combine(workspaceRoot, ".program-kit", "publication.journal.json");
        JsonObject journal = File.Exists(journalPath)
            ? CanonicalJson.Parse(File.ReadAllBytes(journalPath)) as JsonObject
                ?? throw new InvalidDataException("The publication journal is invalid.")
            : throw new InvalidDataException("The publication journal is unavailable.");
        if (!string.Equals(journal["state"]?.GetValue<string>(), "committed", StringComparison.Ordinal)
            || !string.Equals(journal["constructionIdentity"]?.GetValue<string>(), candidate.ConstructionIdentity, StringComparison.Ordinal)
            || !string.Equals(journal["observedLiveState"]?.GetValue<string>(), liveStateDigest, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Admission requires a complete committed publication journal.");
        }
    }

    private static ArtifactReference ReferenceForFile(string workspaceRoot, string logicalPath, string kind, string name)
    {
        string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
        string digest = File.Exists(path)
            ? Digests.Sha256(File.ReadAllBytes(path))
            : throw new FileNotFoundException("An admission artifact is unavailable.", path);
        return new ArtifactReference(
            new GovernedIdentity("orbyss.program-kit", kind, name, "1", digest),
            "application/json",
            logicalPath,
            digest,
            ArtifactOwnership.GeneratedOwned);
    }

    private static string SafeName(string value)
    {
        string safe = new(value.Select(static character => char.IsLetterOrDigit(character) || character is '.' or '-' ? character : '-').ToArray());
        return safe.Length <= 200 ? safe : safe[..200];
    }
}
