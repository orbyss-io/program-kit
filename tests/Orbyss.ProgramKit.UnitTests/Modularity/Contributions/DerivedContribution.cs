namespace Orbyss.ProgramKit.UnitTests.Modularity.Contributions;

internal sealed record DerivedContribution(
    string Value) : BaseContribution(Value);
