namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>One explicit resource readiness dependency.</summary>
public sealed record AspireWaitDependency(
    string SourceResourceName,
    string TargetResourceName);
