using Microsoft.Build.Framework;

namespace Orbyss.ProgramKit.CSharpBuildGates.Build.Operations.Execution;

internal sealed record CSharpBuildGateActivationResult(
    IReadOnlyList<ITaskItem> Applicable,
    IReadOnlyList<(ITaskItem Analyzer, ITaskItem Exception)> Excepted);
