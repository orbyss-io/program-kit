namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed record RecordedContribution(
    string Value) : IDomainContribution;
