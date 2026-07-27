using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Exact compatibility ranges for one gate definition.</summary>
public sealed record CSharpGateCompatibility(
    SemanticVersionRange SdkRange,
    SemanticVersionRange CompilerRoslynRange,
    SemanticVersionRange LanguageRange,
    SemanticVersionRange TargetFrameworkRange,
    SemanticVersionRange ProgramKitMechanicsRange);
