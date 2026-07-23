namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

[TestClass]
public sealed class JsonCompositionSubstitutabilityTests
{
    [TestMethod]
    public void FluentBuilderAndFactoryExposeOnlySubstitutableContracts()
    {
        Assert.AreEqual(
            typeof(IProgramKitJsonBuilder),
            GetBuilderMethod(nameof(IProgramKitJsonBuilder.AddProfile)).ReturnType);
        Assert.AreEqual(
            typeof(IProgramKitJsonBuilder),
            GetBuilderMethod(nameof(IProgramKitJsonBuilder.AddOwnedProfile)).ReturnType);
        Assert.AreEqual(
            typeof(IProgramKitJsonBuilder),
            GetBuilderMethod(
                nameof(IProgramKitJsonBuilder.AddJsonSerializationContribution))
                .ReturnType);
        Assert.AreEqual(
            typeof(IProgramKitJsonRegistry),
            GetBuilderMethod(nameof(IProgramKitJsonBuilder.Freeze)).ReturnType);
        Assert.AreEqual(
            typeof(IProgramKitJsonRegistry),
            typeof(IProgramKitJsonRegistryFactory)
                .GetMethod(nameof(IProgramKitJsonRegistryFactory.Create))!
                .ReturnType);
    }

    [TestMethod]
    public void BuilderAcceptsAnExternalFactoryReturningAnExternalRegistry()
    {
        var expectedRegistry = new StubProgramKitJsonRegistry();
        var factory = new StubProgramKitJsonRegistryFactory(expectedRegistry);
        var builder = new ProgramKitJsonBuilder(factory);

        var (fluentBuilder, registry, repeatedRegistry) =
            FreezeUsingContract(builder);

        Assert.AreSame(builder, fluentBuilder);
        Assert.AreSame(expectedRegistry, registry);
        Assert.AreSame(expectedRegistry, repeatedRegistry);
        Assert.AreEqual(1, factory.CreateCallCount);
    }

    private static (
        IProgramKitJsonBuilder FluentBuilder,
        IProgramKitJsonRegistry Registry,
        IProgramKitJsonRegistry RepeatedRegistry)
        FreezeUsingContract<TBuilder>(TBuilder builder)
        where TBuilder : IProgramKitJsonBuilder
    {
        var fluentBuilder =
            builder.AddProfile(ProgramKitJsonProfiles.JsonContracts);
        return (fluentBuilder, builder.Freeze(), builder.Freeze());
    }

    private static System.Reflection.MethodInfo GetBuilderMethod(string name) =>
        typeof(IProgramKitJsonBuilder).GetMethod(name)
        ?? throw new InvalidOperationException(
            string.Concat("Missing JSON builder method '", name, "'."));
}
