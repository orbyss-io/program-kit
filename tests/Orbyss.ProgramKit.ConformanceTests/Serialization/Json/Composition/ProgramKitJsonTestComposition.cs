namespace Orbyss.ProgramKit.ConformanceTests.Serialization.Json.Composition;

internal static class ProgramKitJsonTestComposition
{
    internal static IProgramKitJsonRegistryFactory CreateRegistryFactory() =>
        new ProgramKitJsonRegistryFactory();

    internal static IProgramKitJsonBuilder CreateBuilder()
    {
        var registryFactory = CreateRegistryFactory();
        return new ProgramKitJsonBuilder(registryFactory);
    }
}
