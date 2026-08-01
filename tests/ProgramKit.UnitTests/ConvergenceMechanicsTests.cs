using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ConvergenceMechanicsTests
{
    [TestMethod]
    public void Provider_role_manifest_must_equal_callable_SPI_surface()
    {
        Assert.ThrowsExactly<InvalidOperationException>(() => new ProviderRegistry(new IFactoryProvider[] { new MisdeclaredProvider() }));
        ProviderRegistry registry = new(new IFactoryProvider[] { new CompleteProvider() });
        Assert.AreEqual(1, registry.All.Count);
    }

    [TestMethod]
    public void Exact_provider_selection_rejects_a_digest_mismatch()
    {
        CompleteProvider provider = new();
        ProviderRegistry registry = new(new IFactoryProvider[] { provider });
        ExactSelection selection = new(
            "construction",
            provider.Manifest.Identity with { Digest = Digest("wrong") },
            Identity("selection", "test"));
        Assert.ThrowsExactly<KeyNotFoundException>(() => registry.ResolveRole<IConstructionProvider>(new[] { selection }, ProviderRole.Construction));
    }

    [TestMethod]
    public void Candidate_sealing_rejects_undeclared_and_case_colliding_artifacts()
    {
        string root = CreateTemp();
        try
        {
            Directory.CreateDirectory(Path.Combine(root, "products"));
            File.WriteAllText(Path.Combine(root, "products", "undeclared.txt"), "content", Encoding.UTF8);
            CandidateArtifactSetBuilder builder = new();
            Assert.ThrowsExactly<InvalidOperationException>(() => builder.Seal(Digest("candidate"), root, Array.Empty<ProviderArtifact>()));

            File.Delete(Path.Combine(root, "products", "undeclared.txt"));
            ProviderArtifact[] collisions =
            {
                new("products/Value.txt", ArtifactOwnership.GeneratedOwned, "text/plain", ClaimClass.CanonicalByte, "test"),
                new("products/value.txt", ArtifactOwnership.GeneratedOwned, "text/plain", ClaimClass.CanonicalByte, "test"),
            };
            Assert.ThrowsExactly<InvalidOperationException>(() => builder.Seal(Digest("candidate"), root, collisions));
        }
        finally
        {
            DeleteTemp(root);
        }
    }

    [TestMethod]
    [DataRow("journal-prepared", "candidate-only")]
    [DataRow("publishing-started", "indeterminate")]
    [DataRow("live-write-completed", "indeterminate")]
    [DataRow("operation-recorded", "indeterminate")]
    [DataRow("before-journal-commit", "indeterminate")]
    public void Every_publication_boundary_is_untrusted_and_rollback_safe(string boundary, string expectedEffect)
    {
        string workspace = CreateTemp();
        try
        {
            CandidateArtifactSet candidate = Candidate(workspace, "new");
            RecoverablePublisher publisher = new(new ThrowAtBoundary(boundary));
            PublicationInterruptedException interrupted = Assert.ThrowsExactly<PublicationInterruptedException>(() =>
                publisher.Publish(workspace, candidate, ConstructionMode.New, Digest(string.Empty)));
            Assert.AreEqual(expectedEffect, Kebab(interrupted.ProvenEffect));
            Assert.IsFalse(File.Exists(Path.Combine(workspace, ".program-kit", "construction-receipt.json")));

            PublicationRecovery recovery = new();
            PublicationRecoveryState inspected = recovery.Inspect(workspace)!;
            Assert.AreEqual(expectedEffect, Kebab(inspected.Effect));
            PublicationRecoveryState rolledBack = recovery.Recover(workspace, PublicationRecoveryStrategy.Rollback, ConstructionMode.Repair);
            Assert.AreEqual("rolled-back", rolledBack.State);
            Assert.AreEqual(EffectState.None, rolledBack.Effect);
            Assert.IsFalse(File.Exists(Path.Combine(workspace, "products", "value.txt")));
        }
        finally
        {
            DeleteTemp(workspace);
        }
    }

    [TestMethod]
    public void Repair_rollback_restores_an_exact_backup_even_before_operation_recording()
    {
        string workspace = CreateTemp();
        try
        {
            string target = Path.Combine(workspace, "products", "value.txt");
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.WriteAllText(target, "old", new UTF8Encoding(false));
            CandidateArtifactSet candidate = Candidate(workspace, "new");
            string expected = LiveState.Compute(workspace, candidate.Artifacts);
            RecoverablePublisher publisher = new(new ThrowAtBoundary("backup-created"));
            Assert.ThrowsExactly<PublicationInterruptedException>(() =>
                publisher.Publish(workspace, candidate, ConstructionMode.Repair, expected));

            PublicationRecoveryState rolledBack = new PublicationRecovery().Recover(
                workspace,
                PublicationRecoveryStrategy.Rollback,
                ConstructionMode.Repair);
            Assert.AreEqual("rolled-back", rolledBack.State);
            Assert.AreEqual("old", File.ReadAllText(target));
        }
        finally
        {
            DeleteTemp(workspace);
        }
    }

    [TestMethod]
    public void Diagnostic_grouping_truncation_and_disclosure_are_deterministic()
    {
        Diagnostic duplicate = DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Validation,
            "factory-request",
            "invalid",
            "revise");
        DiagnosticView grouped = DiagnosticFactory.View(new[] { duplicate, duplicate });
        Assert.AreEqual(1, grouped.Total);
        Assert.AreEqual(2, grouped.Items[0].OccurrenceCount);

        Diagnostic[] many = Enumerable.Range(0, 101).Select(index => DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Validation,
            $"subject-{index:D3}",
            "invalid",
            "revise")).ToArray();
        DiagnosticView truncated = DiagnosticFactory.View(many);
        Assert.AreEqual(101, truncated.Total);
        Assert.AreEqual(100, truncated.Returned);
        Assert.AreEqual(1, truncated.Omitted);
        Assert.AreEqual(truncated.FullCollectionDigest, DiagnosticFactory.View(many.Reverse()).FullCollectionDigest);

        Assert.AreEqual("withheld", DisclosureFilter.SafeText("password=do-not-emit"));
        Assert.AreEqual("withheld", DisclosureFilter.SafeText("C:\\Users\\person\\secret.txt"));
        Assert.AreEqual("withheld", DisclosureFilter.SafeText("System.InvalidOperationException at A.B(C.cs:12)"));
        Assert.AreNotEqual(Digest(string.Empty), ProtocolIdentities.Operation("construct").Digest);
        Assert.IsFalse(ProtocolIdentities.Operation("construct").Digest.EndsWith(new string('0', 64), StringComparison.Ordinal));
    }

    private static CandidateArtifactSet Candidate(string workspace, string content)
    {
        string candidateRoot = Path.Combine(workspace, ".candidate");
        string candidatePath = Path.Combine(candidateRoot, "products", "value.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(candidatePath)!);
        File.WriteAllText(candidatePath, content, new UTF8Encoding(false));
        string digest = Digest(content);
        ArtifactManifestEntry artifact = new(
            "products/value.txt",
            ArtifactOwnership.GeneratedOwned,
            "text/plain",
            digest,
            "test:producer",
            ClaimClass.CanonicalByte);
        return new CandidateArtifactSet(Digest($"construction-{content}"), candidateRoot, new[] { artifact }, Digest($"set-{content}"), CandidateState.Sealed);
    }

    private static string CreateTemp()
    {
        string root = Path.Combine(Path.GetTempPath(), "program-kit-tests", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        return root;
    }

    private static void DeleteTemp(string root)
    {
        if (Directory.Exists(root))
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static GovernedIdentity Identity(string kind, string name) => new("test", kind, name, "1", Digest($"{kind}:{name}"));

    private static string Digest(string value) => Digests.Sha256(Encoding.UTF8.GetBytes(value));

    private static string Kebab<T>(T value)
        where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));

    private sealed class ThrowAtBoundary : IPublicationFaultInjector
    {
        private readonly string boundary;

        public ThrowAtBoundary(string boundary) => this.boundary = boundary;

        public void Observe(string observed, int completedOperations)
        {
            if (string.Equals(boundary, observed, StringComparison.Ordinal))
            {
                throw new IOException($"Injected publication fault at {observed}:{completedOperations}.");
            }
        }
    }

    private sealed class MisdeclaredProvider : IIntakeMappingProvider
    {
        public ProviderManifest Manifest { get; } = ManifestFor(new[] { ProviderRole.Construction });

        public Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context) => throw new NotSupportedException();
    }

    private sealed class CompleteProvider : IIntakeMappingProvider, IConstructionProvider, IEvaluationProvider
    {
        public ProviderManifest Manifest { get; } = ManifestFor(new[] { ProviderRole.IntakeMapping, ProviderRole.Construction, ProviderRole.Evaluation });

        public Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context) => throw new NotSupportedException();

        public Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context) => throw new NotSupportedException();

        public Task<ProviderEvaluationResult> EvaluateAsync(ProviderEvaluationContext context) => throw new NotSupportedException();
    }

    private static ProviderManifest ManifestFor(IReadOnlyList<ProviderRole> roles)
    {
        GovernedIdentity identity = Identity("factory-provider", "test");
        return new ProviderManifest(identity, Identity("distribution", "test"), roles, new[] { "test" }, new[] { "test" }, new[] { "test" }, Array.Empty<string>(), Array.Empty<string>());
    }
}
