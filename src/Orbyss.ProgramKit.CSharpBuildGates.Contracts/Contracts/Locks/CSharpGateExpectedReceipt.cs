using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

/// <summary>Expected same-assembly receipt identity for one covered compilation.</summary>
public sealed record CSharpGateExpectedReceipt(
    ProgramKitIdentifier ProjectProfileId,
    ProgramKitIdentifier AnalyzerComponentId,
    CSharpGateVerificationProfileKind VerificationProfile,
    ProgramKitIdentifier ReceiptIdentity);
