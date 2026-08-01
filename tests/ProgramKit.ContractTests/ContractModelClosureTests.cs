using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Workspace;
using Orbyss.ProgramKit.Kernel.Intake;
using YamlDotNet.Core;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ContractModelClosureTests
{
    [TestMethod]
    public void Public_contract_model_exposes_bounded_safe_values_waivers_and_workspace_records()
    {
        GovernedIdentity identity = Identity("subject");
        ArtifactReference policy = new(identity, "application/json", "policy/waiver.json", identity.Digest, ArtifactOwnership.ConsumerOwned);
        SafeValue visible = new(SafeValueClassification.Public, SafeValueKind.Text, "safe");
        SafeValue withheld = new(SafeValueClassification.Withheld, SafeValueKind.Redacted, null, "secret", identity);

        Assert.AreEqual("safe", visible.Value);
        Assert.IsNull(withheld.Value);
        Assert.ThrowsExactly<ArgumentException>(() => new SafeValue(SafeValueClassification.Public, SafeValueKind.Text, null));
        Assert.ThrowsExactly<ArgumentException>(() => new PolicyWaiver(
            identity,
            identity,
            Array.Empty<GovernedIdentity>(),
            new[] { identity },
            PublicCommand.Construct,
            identity,
            RequestedEffect.Committed,
            visible,
            new[] { visible },
            Array.Empty<EvidenceReference>(),
            policy,
            DateTimeOffset.Parse("2026-08-02T00:00:00Z", System.Globalization.CultureInfo.InvariantCulture)));
        Assert.ThrowsExactly<ArgumentException>(() => new GateResult(
            identity,
            "evidence-backed",
            "waived",
            new[] { identity },
            Array.Empty<EvidenceReference>(),
            Array.Empty<string>()));

        Assert.IsNotNull(typeof(CandidateArtifactSet).GetProperty(nameof(CandidateArtifactSet.Preconditions)));
        Assert.IsNotNull(typeof(CandidateArtifactSet).GetProperty(nameof(CandidateArtifactSet.GateResults)));
        Assert.IsNotNull(typeof(ArtifactManifestEntry).GetProperty(nameof(ArtifactManifestEntry.Sources)));
        Assert.IsNotNull(typeof(AdmissionPublicationReceipt).GetProperty(nameof(AdmissionPublicationReceipt.ObservedLiveState)));
        Assert.IsNotNull(typeof(ArtifactState).GetProperty(nameof(ArtifactState.ObservedDigest)));
        Assert.IsNotNull(typeof(WorkspaceSnapshot).GetProperty(nameof(WorkspaceSnapshot.Trace)));
    }

    [TestMethod]
    public void Restricted_yaml_preserves_only_safe_pointer_spans_and_bounds_scalars()
    {
        const string yaml = "name: value\nnested:\n  enabled: true\nslash/key~: quoted\n";
        RestrictedYamlDocument document = new RestrictedYamlParser().ParseDocument(Encoding.UTF8.GetBytes(yaml));

        CollectionAssert.AreEquivalent(
            new[] { string.Empty, "/name", "/nested", "/nested/enabled", "/slash~1key~0" },
            new List<string>(document.SourceSpans.Keys));
        foreach (SourceSpan span in document.SourceSpans.Values)
        {
            Assert.IsTrue(span.Start.Line > 0);
            Assert.IsTrue(span.Start.Column > 0);
            Assert.IsTrue(span.Start.Offset >= 0);
            Assert.IsTrue(span.End.Offset >= span.Start.Offset);
        }

        string oversized = $"value: {new string('a', 65_537)}";
        Assert.ThrowsExactly<YamlException>(() => new RestrictedYamlParser().Parse(Encoding.UTF8.GetBytes(oversized)));
    }

    private static GovernedIdentity Identity(string name) => new(
        "orbyss.program-kit.tests",
        "contract-test",
        name,
        "1.0.0",
        $"sha256:{new string('1', 64)}");
}
