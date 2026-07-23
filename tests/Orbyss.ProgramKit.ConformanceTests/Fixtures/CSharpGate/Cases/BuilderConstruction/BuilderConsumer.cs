namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.BuilderConstruction;

public sealed class BuilderConsumer
{
    public string Build()
    {
        var builder = new ConfiguredBuilder();
        return builder.Build();
    }
}
