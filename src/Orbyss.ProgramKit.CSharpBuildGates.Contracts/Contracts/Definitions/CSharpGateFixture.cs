using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An exact digest-bound fixture expectation.</summary>
public sealed record CSharpGateFixture(
    ProgramKitIdentifier Identity,
    CSharpGateFixtureKind Kind,
    ArtifactReference Input,
    Sha256Digest ExpectedDiagnosticsDigest,
    Sha256Digest ExpectedEvidenceDigest);
