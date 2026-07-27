using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Selections;

/// <summary>
/// An exact Program Kit-owned public analyzer selection rendered separately
/// from consumer-owned analyzer source.
/// </summary>
public sealed record CSharpPublicAnalyzerSelectionProjection(
    string ComponentIdentity,
    string SemanticOwnerId,
    string PackageIdentity,
    string PackageVersion,
    string PackageSha256,
    string AssemblyPath,
    string AssemblySha256,
    string ContractIdentity,
    string ContractVersion,
    ImmutableArray<string> DiagnosticIds);
