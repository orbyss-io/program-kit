using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

/// <summary>A same-assembly participation receipt from one analyzer.</summary>
public sealed record CSharpGateParticipationReceiptDocument(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ArtifactReference SelectionLock,
    ProgramKitIdentifier ProjectProfileId,
    ProgramKitIdentifier AnalyzerComponentId,
    CSharpGateVerificationProfileKind VerificationProfile,
    string CompilationNonce,
    Sha256Digest AnalyzerAssemblyDigest,
    Sha256Digest ValidatedCompilerInputDigest,
    Sha256Digest ExecutedCompilerInputDigest,
    Sha256Digest CompilationOutputDigest);
