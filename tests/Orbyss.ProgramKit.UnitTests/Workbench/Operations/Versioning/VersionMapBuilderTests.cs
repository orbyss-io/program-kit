namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Versioning;

[TestClass]
public sealed class VersionMapBuilderTests
{
    [TestMethod]
    public void BuildOrdersExactNodesAndTypedEdgesDeterministically()
    {
        var target = CreateManifest(
            "pkid:schema:program-kit:target",
            VersionBoundaryKind.Schema,
            []);
        var source = CreateManifest(
            "pkid:implementation:program-kit:source",
            VersionBoundaryKind.Implementation,
            [
                new VersionRequirement(
                    target.Manifest.Identity,
                    SemanticVersionRange.Parse("[1.0.0]"),
                    target.Manifest.Revision,
                    DependencyExposure.Public,
                    [CompatibilityDimension.WireRead],
                    [Evidence("dependency")]),
            ]);
        var request = new VersionMapBuildRequest(
            [source, target],
            [
                new VersionDependencyDeclaration(
                    ProgramKitIdentifier.Parse("pkid:edge:program-kit:source-target"),
                    source.Manifest.Identity,
                    target.Manifest.Identity,
                    VersionDependencyKind.Reads),
            ]);
        var sut = CreateBuilder();

        var first = sut.Build(request);
        var second = sut.Build(request with
        {
            Manifests = [target, source],
        });

        Assert.IsTrue(first.IsSuccessful, Format(first.Validation));
        Assert.IsTrue(second.IsSuccessful, Format(second.Validation));
        Assert.IsNotNull(first.Value);
        Assert.IsNotNull(second.Value);
        Assert.AreSequenceEqual(
            first.Value.Nodes.Select(static node => node.Revision.Identity.Value).ToArray(),
            second.Value.Nodes.Select(static node => node.Revision.Identity.Value).ToArray());
        Assert.AreEqual(VersionDependencyKind.Reads, first.Value.Edges[0].Kind);
        Assert.AreEqual(target.Manifest.Revision, first.Value.Edges[0].Resolution);
        Assert.AreEqual(source.Manifest.Revision, first.Value.Edges[0].Source);
    }

    [TestMethod]
    public void BuildFailsClosedForUnknownCompatibility()
    {
        var input = CreateManifest(
            "pkid:contract:program-kit:unknown",
            VersionBoundaryKind.Contract,
            []) with
        {
            Manifest = CreateManifest(
                "pkid:contract:program-kit:unknown",
                VersionBoundaryKind.Contract,
                []).Manifest with
            {
                CompatibilityClaims =
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.SemanticBehavior,
                        CompatibilityClassification.Unknown,
                        []),
                ],
            },
        };
        var sut = CreateBuilder();

        var result = sut.Build(new VersionMapBuildRequest([input], []));

        Assert.IsFalse(result.IsSuccessful);
        Assert.IsTrue(result.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.InvalidVersionMapBuild));
    }

    private static VersionMapBuilder CreateBuilder()
    {
        IProgramKitSemanticValidator<VersionedComponentManifest> manifestValidator =
            new VersionedComponentManifestValidator();
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        IProgramKitSemanticValidator<VersionMapDocument> mapValidator =
            new VersionMapDocumentValidator(envelopeValidator);
        return new VersionMapBuilder(manifestValidator, mapValidator);
    }

    private static VersionedManifestInput CreateManifest(
        string identity,
        VersionBoundaryKind kind,
        ImmutableArray<VersionRequirement> requirements)
    {
        var parsedIdentity = ProgramKitIdentifier.Parse(identity);
        var manifest = new VersionedComponentManifest(
            parsedIdentity,
            kind,
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
            SemanticVersion.Parse("1.0.0"),
            TestContractValues.Digest,
            [],
            requirements,
            [
                new CompatibilityClaim(
                    CompatibilityDimension.SemanticBehavior,
                    CompatibilityClassification.Editorial,
                    []),
            ],
            []);
        return new VersionedManifestInput(
            Evidence(string.Concat(parsedIdentity.Name, "-manifest")),
            manifest);
    }

    private static ArtifactReference Evidence(string name) =>
        TestContractValues.Reference(string.Concat("pkid:evidence:program-kit:", name));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(diagnostic.Id, " ", diagnostic.Path, " ", diagnostic.Message)));
}
