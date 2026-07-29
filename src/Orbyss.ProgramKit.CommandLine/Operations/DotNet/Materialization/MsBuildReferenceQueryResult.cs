using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Exact reference items returned by one finite MSBuild query.</summary>
public sealed record MsBuildReferenceQueryResult(
    string TargetAssemblyPath,
    string TargetReferencePath,
    ImmutableArray<string> CompilationReferencePaths);
