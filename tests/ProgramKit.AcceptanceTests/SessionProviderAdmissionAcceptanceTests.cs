using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionProviderAdmissionAcceptanceTests
{
    [TestMethod]
    public void Production_admission_invokes_the_declared_conformance_profile()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string request = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root).Explain;
        CodexSessionProviderAdapter reference = new();
        ISessionProviderAdapter[] invalid =
        {
            new AdapterOverride(reference, reference.Manifest with { CanonicalProfile = "program-kit.canonical-json/v2" }),
            new AdapterOverride(reference, reference.Manifest with { SupportedScopes = Array.Empty<string>() }),
            new AdapterOverride(reference, reference.Manifest with { RequiredCliOperations = reference.Manifest.RequiredCliOperations.Where(static item => item != "evaluate").ToArray() }),
            new AdapterOverride(reference, reference.Manifest with { ProjectionDescriptors = reference.Manifest.ProjectionDescriptors.Select(static item => item with { Ownership = ArtifactOwnership.ConsumerOwned }).ToArray() }),
            new AdapterOverride(reference, reference.Manifest with { DiagnosticCatalog = reference.Manifest.DiagnosticCatalog with { Kind = "different-catalog" } }),
            new AdapterOverride(reference, reference.Manifest with { SupportClaim = SessionProviderSupport.Incompatible }),
            new AdapterOverride(reference, reference.Manifest, removeGuarantee: "disclosure=classified"),
            new AdapterOverride(reference, reference.Manifest, removeGuarantee: "authority=request-bound"),
            new AdapterOverride(reference, reference.Manifest, removeGuarantee: "normalization=canonical-json"),
        };

        for (int index = 0; index < invalid.Length; index++)
        {
            SessionIntegrationServices services = new(new SessionProviderRegistry(new[] { invalid[index] }), "1.0.0-alpha.1");
            OperationResult result = SessionFailureBoundary.Execute(
                PublicCommand.SessionExplain,
                () => new ExplainSessionIntegrationOperation(services).Execute(workspace.Root, request));
            Assert.AreEqual(OperationOutcome.Blocked, result.Outcome, $"adapter {index}");
            Assert.AreEqual(EffectState.None, result.EffectState, $"adapter {index}");
            Assert.AreEqual("program-kit.session/PKSES0003", result.Diagnostics.Items[0].Id, $"adapter {index}");
        }
    }

    [TestMethod]
    public void Divergent_definition_binding_is_unavailable_not_ambiently_substituted()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string request = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root).Explain;
        CodexSessionProviderAdapter reference = new();
        ISessionProviderAdapter divergent = new AdapterOverride(reference, reference.Manifest with
        {
            DefinitionBinding = reference.Manifest.DefinitionBinding with { Digest = "sha256:" + new string('6', 64) },
        });
        SessionIntegrationServices services = new(new SessionProviderRegistry(new[] { divergent }), "1.0.0-alpha.1");

        OperationResult result = SessionFailureBoundary.Execute(
            PublicCommand.SessionExplain,
            () => new ExplainSessionIntegrationOperation(services).Execute(workspace.Root, request));
        Assert.AreEqual(OperationOutcome.Blocked, result.Outcome);
        Assert.AreEqual("program-kit.session/PKSES0002", result.Diagnostics.Items[0].Id);
        Assert.AreEqual(PrimaryDisposition.ProvideInput, result.PrimaryDisposition);
        Assert.AreEqual(EffectState.None, result.EffectState);
    }

    private sealed class AdapterOverride : ISessionProviderAdapter
    {
        private readonly ISessionProviderAdapter inner;
        private readonly string? removeGuarantee;

        public AdapterOverride(ISessionProviderAdapter inner, SessionProviderManifest manifest, string? removeGuarantee = null)
        {
            this.inner = inner;
            Manifest = manifest;
            this.removeGuarantee = removeGuarantee;
        }

        public SessionProviderManifest Manifest { get; }

        public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
        {
            IReadOnlyList<ProjectedSessionArtifact> artifacts = inner.Project(context);
            if (removeGuarantee is null) return artifacts;
            return artifacts.Select(artifact => artifact with
            {
                Content = Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(artifact.Content).Replace(removeGuarantee, "removed-guarantee", StringComparison.Ordinal)),
            }).ToArray();
        }
    }
}
