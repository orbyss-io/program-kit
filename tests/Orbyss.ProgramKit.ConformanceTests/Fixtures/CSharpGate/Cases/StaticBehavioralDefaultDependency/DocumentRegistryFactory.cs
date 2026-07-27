namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.StaticBehavioralDefaultDependency;

public sealed class DocumentRegistryFactory : IDocumentRegistryFactory
{
    public static IDocumentRegistryFactory Default { get; } =
        new DocumentRegistryFactory();

    public void Create()
    {
    }
}
