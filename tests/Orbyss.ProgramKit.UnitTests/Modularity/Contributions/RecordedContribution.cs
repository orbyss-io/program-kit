namespace Orbyss.ProgramKit.UnitTests.Modularity.Contributions;

internal sealed record RecordedContribution(
    string Value) : IDomainContribution;
