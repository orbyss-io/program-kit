namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.PropertyOnlyBehavioralRecordReturn;

internal sealed record PropertyOnlyRegistry : IPropertyOnlyRegistry
{
    public int Count { get; init; }
}
