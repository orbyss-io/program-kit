using System.Text;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

[TestClass]
public sealed class ProgramKitJsonSerializerTests
{
    [TestMethod]
    public void SourceGeneratedMetadataAndTypedConverterRoundTripCanonically()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonContributionTestFactory.CreateResolverContribution(
                "probe-metadata",
                "1"));
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            new TypedJsonConverterContribution<ProbeId>(
                JsonContributionTestFactory.CreateDescriptor(
                    "probe-id-converter",
                    "2",
                    JsonSerializationContributionKind.TypedConverter,
                    JsonTargetTypeClaim.For<ProbeId>()),
                new ProbeIdConverter()));
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
        var model = new ProbeModel(
            "z-value",
            7,
            new ProbeId("id-42"));

        var canonical = serializer.Write(
            model,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);
        var observed = serializer.Read<ProbeModel>(
            """{"z":"z-value","id":"id-42","a":7}"""u8.ToArray(),
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);

        Assert.AreEqual(
            """{"a":7,"id":"id-42","z":"z-value"}""",
            Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.AreEqual(model, observed);
    }

    [TestMethod]
    public void SerializerUsesOnlyItsInjectedCanonicalizer()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonContributionTestFactory.CreateResolverContribution(
                "isolated-canonicalizer-metadata",
                "6"));
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            new TypedJsonConverterContribution<ProbeId>(
                JsonContributionTestFactory.CreateDescriptor(
                    "isolated-canonicalizer-probe-id",
                    "7",
                    JsonSerializationContributionKind.TypedConverter,
                    JsonTargetTypeClaim.For<ProbeId>()),
                new ProbeIdConverter()));
        var registry = builder.Freeze();
        var limits = JsonSerializationLimits.Default;
        var expected = new ProbeModel(
            "from-injected-canonicalizer",
            11,
            new ProbeId("injected"));

        var readResult = canonicalizer.Canonicalize(
            """{"a":11,"id":"injected","z":"from-injected-canonicalizer"}"""u8,
            limits);
        var readCanonicalizer = new StubJsonCanonicalizer(readResult);
        var readSerializer = new ProgramKitJsonSerializer(
            registry,
            readCanonicalizer);
        var deliberatelyInvalidInput = "not-json"u8.ToArray();
        var observed = readSerializer.Read<ProbeModel>(
            deliberatelyInvalidInput,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            limits);
        Assert.AreEqual(expected, observed);
        Assert.AreEqual(1, readCanonicalizer.CanonicalizeCallCount);
        Assert.AreSame(limits, readCanonicalizer.LastLimits);
        Assert.IsNotNull(readCanonicalizer.LastInput);
        Assert.AreSequenceEqual(
            deliberatelyInvalidInput,
            readCanonicalizer.LastInput);

        var writeResult = canonicalizer.Canonicalize(
            "\"injected-result\""u8,
            limits);
        var writeCanonicalizer = new StubJsonCanonicalizer(writeResult);
        var writeSerializer = new ProgramKitJsonSerializer(
            registry,
            writeCanonicalizer);
        var canonical = writeSerializer.Write(
            expected,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            limits);
        Assert.AreSequenceEqual(
            writeResult.ToArray(),
            canonical.ToArray());
        Assert.AreEqual(1, writeCanonicalizer.CanonicalizeCallCount);
        Assert.AreSame(limits, writeCanonicalizer.LastLimits);
        Assert.IsNotNull(writeCanonicalizer.LastInput);
        Assert.IsNotEmpty(writeCanonicalizer.LastInput);
    }

    [TestMethod]
    public void DeclaredConverterFactoryFamilyComposesWithSourceGeneratedMetadata()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var resolver =
            JsonContributionTestFactory.CreateResolverContribution(
                "probe-metadata",
                "1",
                typeof(FactoryModel));
        var factory = new JsonConverterFactoryContribution(
            JsonContributionTestFactory.CreateDescriptor(
                "probe-factory",
                "3",
                JsonSerializationContributionKind.ConverterFactory,
                JsonTargetTypeClaim.For<FactoryValue>()),
            new ProbeConverterFactory(),
            typeof(FactoryValue));
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            resolver);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            factory);
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);

        var canonical = serializer.Write(
            new FactoryModel(new FactoryValue("factory")),
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);

        Assert.AreEqual(
            """{"value":"factory"}""",
            Encoding.UTF8.GetString(canonical.ToArray()));
    }

    [TestMethod]
    public void MetaProfileRoundTripsSelectionBeforeConsumerContributions()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
        var selection = new JsonSerializationProfileSelection(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            []);

        var canonical = serializer.Write(
            selection,
            ProgramKitJsonProfiles.JsonMeta.Reference,
            JsonSerializationLimits.Default);
        var observed =
            serializer.Read<JsonSerializationProfileSelection>(
                canonical.ToArray(),
                ProgramKitJsonProfiles.JsonMeta.Reference,
                JsonSerializationLimits.Default);

        Assert.AreEqual(selection, observed);
    }
}
