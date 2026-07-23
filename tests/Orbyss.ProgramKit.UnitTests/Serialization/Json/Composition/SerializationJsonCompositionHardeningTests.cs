using System.Collections.Immutable;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

[TestClass]
public sealed class SerializationJsonCompositionHardeningTests
{
    private static readonly ProgramKitIdentifier TestPackage = new("pkid:package:tests:serialization-hardening");

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public void FixedProfilesCanOwnMetadataAndConvertersWithoutBecomingExtensible()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var profile = CreateProfile("fixed-owned-mechanics", JsonProfileExtensibility.None, 'a');
        var mechanics = new JsonProfileOwnedMechanics(profile.Reference, TestPackage, FixedOwnedJsonContext.Default, new JsonProfileOwnedConverter(new FixedOwnedStateConverter()));
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddOwnedProfile(profile, mechanics);
        var registry = builder.Freeze();
        var serializer = new ProgramKitJsonSerializer(
            registry,
            canonicalizer);
        var canonical = serializer.Write(new FixedOwnedModel("owned", FixedOwnedState.Ready), profile.Reference, JsonSerializationLimits.Default);
        Assert.AreEqual("""{"name":"owned","state":"ready"}""", Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.AreEqual(new FixedOwnedModel("owned", FixedOwnedState.Ready), serializer.Read<FixedOwnedModel>(canonical.ToArray(), profile.Reference, JsonSerializationLimits.Default));
        var contribution = new TypedJsonConverterContribution<BoundaryToken>(Descriptor("fixed-consumer-converter", 'b', JsonSerializationContributionKind.TypedConverter, profile.Reference, typeof(BoundaryToken)), new BoundaryTokenConverter());
        var rejectingBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        rejectingBuilder.AddOwnedProfile(profile, mechanics);
        rejectingBuilder.AddJsonSerializationContribution(profile.Reference, contribution);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(rejectingBuilder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.NonExtensibleProfile, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void ContributionConstructionBindsDescriptorsToExactRuntimeTargets()
    {
        var mismatch = Assert.ThrowsExactly<ProgramKitJsonException>(() => new JsonTypeInfoResolverContribution(Descriptor("resolver-mismatch", 'c', JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), DateConventionJsonContext.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, mismatch.Diagnostic.Id);
        var factoryMismatch = Assert.ThrowsExactly<ProgramKitJsonException>(() => new JsonConverterFactoryContribution(Descriptor("factory-mismatch", 'd', JsonSerializationContributionKind.ConverterFactory, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), new DeclaredOnlyFactory(), typeof(BoundaryToken)));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, factoryMismatch.Diagnostic.Id);
    }

    [TestMethod]
    public void PublicCompositionBoundaryCannotAcceptArbitraryInterfaceImplementations()
    {
        var contributionParameter = typeof(ProgramKitJsonBuilder).GetMethod(nameof(ProgramKitJsonBuilder.AddJsonSerializationContribution), BindingFlags.Instance | BindingFlags.Public)!.GetParameters()[1];
        Assert.AreEqual(typeof(JsonSerializationContribution), contributionParameter.ParameterType);
        var baseConstructors = typeof(JsonSerializationContribution).GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        Assert.IsNotEmpty(baseConstructors);
        Assert.IsTrue(baseConstructors.All(static constructor => !constructor.IsPublic && !constructor.IsFamily && !constructor.IsFamilyOrAssembly));
        var resolverConstructor = typeof(JsonTypeInfoResolverContribution).GetConstructors().Single();
        Assert.AreEqual(typeof(JsonSerializerContext), resolverConstructor.GetParameters()[1].ParameterType);
    }

    [TestMethod]
    public void MetadataAndConverterMayIntentionallyClaimTheSameTarget()
    {
        var resolver = new JsonTypeInfoResolverContribution(Descriptor("overlap-metadata", 'e', JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), BoundaryTokenJsonContext.Default);
        var converter = new TypedJsonConverterContribution<BoundaryToken>(Descriptor("overlap-converter", 'f', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), new BoundaryTokenConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            resolver);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        var registry = builder.Freeze();
        var selection = registry.Selections.Single(static candidate => candidate.Profile == ProgramKitJsonProfiles.JsonContracts.Reference);
        Assert.HasCount(2, selection.Contributions);
    }

    [TestMethod]
    public void CompetingConvertersRequireExplicitPrecedence()
    {
        var firstIdentity = new ProgramKitIdentifier("pkid:json-contribution:tests:first-boundary-converter");
        var secondIdentity = new ProgramKitIdentifier("pkid:json-contribution:tests:second-boundary-converter");
        var first = new TypedJsonConverterContribution<BoundaryToken>(Descriptor(firstIdentity, '1', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, [secondIdentity], [], typeof(BoundaryToken)), new BoundaryTokenConverter());
        var second = new TypedJsonConverterContribution<BoundaryToken>(Descriptor(secondIdentity, '2', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, [], [], typeof(BoundaryToken)), new BoundaryTokenConverter());
        var orderedBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        orderedBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            second);
        orderedBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            first);
        _ = orderedBuilder.Freeze();
        var unorderedFirst = new TypedJsonConverterContribution<BoundaryToken>(Descriptor("unordered-first", '3', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), new BoundaryTokenConverter());
        var unorderedSecond = new TypedJsonConverterContribution<BoundaryToken>(Descriptor("unordered-second", '4', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(BoundaryToken)), new BoundaryTokenConverter());
        var unorderedBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        unorderedBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            unorderedFirst);
        unorderedBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            unorderedSecond);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            unorderedBuilder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.ContributionConflict, exception.Diagnostic.Id);
    }

    [TestMethod]
    [DataRow(true)]
    [DataRow(false)]
    public void ExplicitRootOwnershipSelectsTheClaimingContextInEitherResolverOrder(
        bool containerFirst)
    {
        var containerIdentity = new ProgramKitIdentifier(
            "pkid:json-contribution:tests:container-root");
        var sharedIdentity = new ProgramKitIdentifier(
            "pkid:json-contribution:tests:shared-root");
        var container = new JsonTypeInfoResolverContribution(
            Descriptor(
                containerIdentity,
                'e',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                containerFirst ? [sharedIdentity] : [],
                containerFirst ? [] : [sharedIdentity],
                typeof(ResolverOwnedContainer)),
            ContainerRootJsonContext.Default);
        var shared = new JsonTypeInfoResolverContribution(
            Descriptor(
                sharedIdentity,
                'f',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                [],
                [],
                typeof(ResolverOwnedShared)),
            SharedRootJsonContext.Default);
        var reachableShared =
            ContainerRootJsonContext.Default.GetTypeInfo(
                typeof(ResolverOwnedShared));
        Assert.IsNotNull(reachableShared);
        Assert.AreSame(
            ContainerRootJsonContext.Default,
            reachableShared.OriginatingResolver);

        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            shared);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            container);
        var registry = builder.Freeze();
        var selection = registry.Selections.Single(static candidate =>
            candidate.Profile ==
            ProgramKitJsonProfiles.JsonContracts.Reference);
        Assert.AreEqual(
            containerFirst ? containerIdentity : sharedIdentity,
            selection.Contributions[0].Identity);

        var sharedRoot = registry.GetTypeInfo<ResolverOwnedShared>(
            ProgramKitJsonProfiles.JsonContracts.Reference);
        Assert.AreSame(
            SharedRootJsonContext.Default,
            sharedRoot.OriginatingResolver);
        IProgramKitJsonCanonicalizer canonicalizer =
            new ProgramKitJsonCanonicalizer();
        var serializer = new ProgramKitJsonSerializer(
            registry,
            canonicalizer);
        var sharedModel = new ResolverOwnedShared("root");
        var sharedJson = serializer.Write(
            sharedModel,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);
        Assert.AreEqual(
            sharedModel,
            serializer.Read<ResolverOwnedShared>(
                sharedJson.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
        var containerModel = new ResolverOwnedContainer(
            new ResolverOwnedShared("combined"));
        var containerJson = serializer.Write(
            containerModel,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);
        Assert.AreEqual(
            containerModel,
            serializer.Read<ResolverOwnedContainer>(
                containerJson.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
    }

    [TestMethod]
    public void DirectlyOverlappingResolverRootsHonorExplicitPrecedence()
    {
        var preferredIdentity = new ProgramKitIdentifier(
            "pkid:json-contribution:tests:preferred-shared-root");
        var fallbackIdentity = new ProgramKitIdentifier(
            "pkid:json-contribution:tests:fallback-shared-root");
        var preferred = new JsonTypeInfoResolverContribution(
            Descriptor(
                preferredIdentity,
                '7',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                [fallbackIdentity],
                [],
                typeof(ResolverOwnedShared)),
            AlternateSharedRootJsonContext.Default);
        var fallback = new JsonTypeInfoResolverContribution(
            Descriptor(
                fallbackIdentity,
                '8',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                [],
                [],
                typeof(ResolverOwnedShared)),
            SharedRootJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            fallback);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            preferred);
        var registry = builder.Freeze();

        var sharedRoot = registry.GetTypeInfo<ResolverOwnedShared>(
            ProgramKitJsonProfiles.JsonContracts.Reference);
        Assert.AreSame(
            AlternateSharedRootJsonContext.Default,
            sharedRoot.OriginatingResolver);
    }

    [TestMethod]
    public void SingleContainerResolverRetainsReachableNestedMetadata()
    {
        var container = new JsonTypeInfoResolverContribution(
            Descriptor(
                "standalone-container-root",
                '9',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(ResolverOwnedContainer)),
            ContainerRootJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            container);
        IProgramKitJsonCanonicalizer canonicalizer =
            new ProgramKitJsonCanonicalizer();
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
        var model = new ResolverOwnedContainer(
            new ResolverOwnedShared("nested"));

        var canonical = serializer.Write(
            model,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);
        Assert.AreEqual(
            """{"shared":{"value":"nested"}}""",
            Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.AreEqual(
            model,
            serializer.Read<ResolverOwnedContainer>(
                canonical.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
    }

    [TestMethod]
    public void ConsumerConvertersCannotReplaceBuiltInPrimitiveMechanics()
    {
        var contribution = new TypedJsonConverterContribution<ProgramKitIdentifier>(Descriptor("identifier-replacement", '5', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(ProgramKitIdentifier)), new IdentifierReplacementConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            contribution);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(builder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.ContributionConflict, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void ConverterFactoryCannotInterceptAnUndeclaredRuntimeTarget()
    {
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var factory = new BroadFactory();
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "factory-boundary-metadata",
                '6',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(FactoryBoundaryModel)),
            FactoryBoundaryJsonContext.Default);
        var declaredFactory = new JsonConverterFactoryContribution(
            Descriptor(
                "broad-factory",
                '7',
                JsonSerializationContributionKind.ConverterFactory,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(DeclaredFactoryValue)),
            factory,
            typeof(DeclaredFactoryValue));
        var foreignConverter =
            new TypedJsonConverterContribution<ForeignFactoryValue>(
                Descriptor(
                    "foreign-factory-value",
                    '8',
                    JsonSerializationContributionKind.TypedConverter,
                    ProgramKitJsonProfiles.JsonContracts.Reference,
                    typeof(ForeignFactoryValue)),
                new ForeignFactoryValueConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            declaredFactory);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            foreignConverter);
        factory.ClearObservedTypes();
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            canonicalizer);
        var observedDuringFreeze = factory.ObservedTypes.Count;
        var canonical = serializer.Write(new FactoryBoundaryModel(new DeclaredFactoryValue("declared"), new ForeignFactoryValue("foreign")), ProgramKitJsonProfiles.JsonContracts.Reference, JsonSerializationLimits.Default);
        Assert.AreEqual("""{"declared":"declared","foreign":"foreign"}""", Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.IsTrue(factory.ObservedTypes.All(static type => type == typeof(DeclaredFactoryValue)));
        Assert.HasCount(observedDuringFreeze, factory.ObservedTypes);
        Assert.DoesNotContain(
            typeof(ForeignFactoryValue),
            factory.ObservedTypes);
        var undeclaredRoot = Assert.ThrowsExactly<ProgramKitJsonException>(() => serializer.Write(new DeclaredFactoryValue("nested-only"), ProgramKitJsonProfiles.JsonContracts.Reference, JsonSerializationLimits.Default));
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable, undeclaredRoot.Diagnostic.Id);
    }

    [TestMethod]
    public void RejectingOpenGenericFactoryFallsBackToValidatedGeneratedMetadata()
    {
        var rootType =
            typeof(OpenGenericFallbackContainer<BoundaryToken>);
        var factory = new RejectingOpenGenericListFactory();
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "open-generic-fallback-metadata",
                'a',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                rootType),
            ValidOpenGenericFallbackJsonContext.Default);
        var factoryContribution = new JsonConverterFactoryContribution(
            Descriptor(
                "rejecting-open-generic-list",
                'b',
                JsonSerializationContributionKind.ConverterFactory,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(List<>)),
            factory,
            typeof(List<>));
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            factoryContribution);

        var registry = builder.Freeze();
        Assert.Contains(
            typeof(List<BoundaryToken>),
            factory.ObservedTypes);
        var observedDuringFreeze = factory.ObservedTypes.Count;
        var serializer = new ProgramKitJsonSerializer(
            registry,
            new ProgramKitJsonCanonicalizer());
        var canonical = serializer.Write(
            new OpenGenericFallbackContainer<BoundaryToken>(
                [new BoundaryToken("fallback")]),
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);

        Assert.AreEqual(
            """{"items":[{"Value":"fallback"}]}""",
            Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.HasCount(observedDuringFreeze, factory.ObservedTypes);
    }

    [TestMethod]
    public void RejectingOpenGenericFactoryCannotHideInvalidFallbackMetadata()
    {
        var rootType =
            typeof(OpenGenericFallbackContainer<NumberHandlingOverrideModel>);
        var factory = new RejectingOpenGenericListFactory();
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "invalid-open-generic-fallback-metadata",
                'c',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                rootType),
            InvalidOpenGenericFallbackJsonContext.Default);
        var factoryContribution = new JsonConverterFactoryContribution(
            Descriptor(
                "rejecting-open-generic-list-invalid-fallback",
                'd',
                JsonSerializationContributionKind.ConverterFactory,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(List<>)),
            factory,
            typeof(List<>));
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            factoryContribution);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "member-level JSON convention override",
            exception.Diagnostic.Message);
        Assert.Contains(
            typeof(List<NumberHandlingOverrideModel>),
            factory.ObservedTypes);
    }

    [TestMethod]
    public void SourceGeneratedPolymorphismIsRejectedDuringFreeze()
    {
        var contribution = new JsonTypeInfoResolverContribution(Descriptor("polymorphic-metadata", '9', JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(PolymorphicBoundary)), PolymorphicBoundaryJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            contribution);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(builder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void DateWireConventionRequiresAnExactConverterContribution()
    {
        var metadata = new JsonTypeInfoResolverContribution(Descriptor("date-metadata", 'a', JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(DateConventionModel)), DateConventionJsonContext.Default);
        var metadataOnlyBuilder =
            ProgramKitJsonTestComposition.CreateBuilder();
        metadataOnlyBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            metadataOnlyBuilder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, exception.Diagnostic.Id);
        var converter = new TypedJsonConverterContribution<DateTime>(Descriptor("date-converter", 'b', JsonSerializationContributionKind.TypedConverter, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(DateTime)), new ExactDateTimeConverter());
        var validBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        validBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        validBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        _ = validBuilder.Freeze();
    }

    [TestMethod]
    public void DecimalWireConventionRequiresVersionedStringMechanicsAndPreservesPrecision()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "decimal-metadata",
                '8',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(DecimalConventionModel)),
            DecimalConventionJsonContext.Default);
        var metadataOnlyBuilder =
            ProgramKitJsonTestComposition.CreateBuilder();
        metadataOnlyBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            metadataOnlyBuilder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            typeof(decimal).FullName!,
            exception.Diagnostic.Message);
        Assert.Contains(
            "schema-constrained strings",
            exception.Diagnostic.Message);

        var converter = new TypedJsonConverterContribution<decimal>(
            Descriptor(
                "decimal-string-converter",
                '7',
                JsonSerializationContributionKind.TypedConverter,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(decimal)),
            new ExactDecimalStringConverter());
        var validBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        validBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        validBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        var serializer = new ProgramKitJsonSerializer(
            validBuilder.Freeze(),
            new ProgramKitJsonCanonicalizer());
        var model = new DecimalConventionModel(0.10000000000000001m);

        var canonical = serializer.Write(
            model,
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);
        var observed = serializer.Read<DecimalConventionModel>(
            canonical.ToArray(),
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonSerializationLimits.Default);

        Assert.AreEqual(
            """{"amount":"0.10000000000000001"}""",
            Encoding.UTF8.GetString(canonical.ToArray()));
        Assert.AreEqual(model, observed);
    }

    [TestMethod]
    public void LossyNumericDecimalConverterCannotCrossTheExactStringBoundary()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "lossy-decimal-metadata",
                '6',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(DecimalConventionModel)),
            DecimalConventionJsonContext.Default);
        var converter = new TypedJsonConverterContribution<decimal>(
            Descriptor(
                "lossy-decimal-converter",
                '5',
                JsonSerializationContributionKind.TypedConverter,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(decimal)),
            new LossyNumericDecimalConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);
        var serializer = new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
        var model = new DecimalConventionModel(0.10000000000000001m);

        var writeException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            serializer.Write(
                model,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));
        var readException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            serializer.Read<DecimalConventionModel>(
                """{"amount":0.10000000000000001}"""u8.ToArray(),
                ProgramKitJsonProfiles.JsonContracts.Reference,
                JsonSerializationLimits.Default));

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            writeException.Diagnostic.Id);
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            readException.Diagnostic.Id);
    }

    [TestMethod]
    public void SelectedConvertersCannotMaskMemberLevelConventionOverrides()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "masked-member-override-metadata",
                '4',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(PropertyConverterOverrideModel)),
            PropertyConverterJsonContext.Default);
        var converter = new TypedJsonConverterContribution<BoundaryToken>(
            Descriptor(
                "masked-member-override-converter",
                '3',
                JsonSerializationContributionKind.TypedConverter,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(BoundaryToken)),
            new BoundaryTokenConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "member-level JSON convention override",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public void SelectedConvertersCannotMaskContractLevelConventionOverrides()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "masked-contract-override-metadata",
                '6',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(ContractOverrideValue)),
            ContractConverterJsonContext.Default);
        var converter =
            new TypedJsonConverterContribution<ContractOverrideValue>(
                Descriptor(
                    "masked-contract-override-converter",
                    '7',
                    JsonSerializationContributionKind.TypedConverter,
                    ProgramKitJsonProfiles.JsonContracts.Reference,
                    typeof(ContractOverrideValue)),
                new ContractOverrideConverter());
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            converter);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "contract-level JSON convention override",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public void SourceGeneratedUntypedContractRootIsRejected()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "untyped-contract-root",
                '8',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(object)),
            UntypedObjectJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "untyped JSON mechanics type",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public void SourceGeneratedDomContractRootsAreRejected()
    {
        var jsonAssembly = typeof(Utf8JsonReader).Assembly;
        var targetNames = new[]
        {
            string.Concat("System.Text.Json.", "Json", "Element"),
            string.Concat("System.Text.Json.", "Json", "Document"),
            string.Concat("System.Text.Json.Nodes.", "Json", "Node"),
        };
        foreach (var targetName in targetNames)
        {
            var target = jsonAssembly.GetType(
                targetName,
                throwOnError: true)!;
            var context = DynamicJsonContextFactory.Create(target);
            var metadata = new JsonTypeInfoResolverContribution(
                Descriptor(
                    string.Concat(
                        "untyped-contract-root-",
                        target.Name.ToLowerInvariant()),
                    'a',
                    JsonSerializationContributionKind.TypeInfoResolver,
                    ProgramKitJsonProfiles.JsonContracts.Reference,
                    target),
                context);
            var builder = ProgramKitJsonTestComposition.CreateBuilder();
            builder.AddJsonSerializationContribution(
                ProgramKitJsonProfiles.JsonContracts.Reference,
                metadata);

            var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
                builder.Freeze);

            Assert.AreEqual(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                exception.Diagnostic.Id,
                targetName);
            Assert.Contains(
                "untyped JSON mechanics type",
                exception.Diagnostic.Message,
                targetName);
        }
    }

    [TestMethod]
    public void SourceGeneratedContractAndMemberOverridesAreRejected()
    {
        var cases = new (string Name, char Digest, Type Target, JsonSerializerContext Context)[]
        {
            ("contract-converter", 'c', typeof(ContractOverrideValue), ContractConverterJsonContext.Default),
            ("property-converter", 'd', typeof(PropertyConverterOverrideModel), PropertyConverterJsonContext.Default),
            ("number-handling", 'e', typeof(NumberHandlingOverrideModel), NumberHandlingJsonContext.Default),
            ("extension-data", 'f', typeof(ExtensionDataOverrideModel), ExtensionDataJsonContext.Default),
            ("ignore-null", '1', typeof(IgnoreNullOverrideModel), IgnoreNullJsonContext.Default),
        };
        foreach (var testCase in cases)
        {
            var contribution = new JsonTypeInfoResolverContribution(Descriptor(testCase.Name, testCase.Digest, JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, testCase.Target), testCase.Context);
            var builder = ProgramKitJsonTestComposition.CreateBuilder();
            builder.AddJsonSerializationContribution(
                ProgramKitJsonProfiles.JsonContracts.Reference,
                contribution);
            var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
                builder.Freeze);
            Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, exception.Diagnostic.Id, testCase.Name);
        }
    }

    [TestMethod]
    public void GeneratedContextOptionsMustMatchTheSelectedProfile()
    {
        var contribution = new JsonTypeInfoResolverContribution(Descriptor("context-options", '2', JsonSerializationContributionKind.TypeInfoResolver, ProgramKitJsonProfiles.JsonContracts.Reference, typeof(ContextOptionsModel)), MismatchedOptionsJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            contribution);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(builder.Freeze);
        Assert.AreEqual(ProgramKitJsonDiagnosticIds.InvalidContribution, exception.Diagnostic.Id);
    }

    [TestMethod]
    public void SerializationOnlyGeneratedContextsAreRejected()
    {
        var contribution = new JsonTypeInfoResolverContribution(
            Descriptor(
                "serialization-only-context",
                '9',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(ContextOptionsModel)),
            SerializationOnlyJsonContext.Default);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            contribution);

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "options that differ",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public void PublicFactoryRejectsConsumerOwnedMechanicsForBuiltInProfiles()
    {
        var replacement = new JsonProfileOwnedMechanics(
            ProgramKitJsonProfiles.JsonMeta.Reference,
            TestPackage,
            FixedOwnedJsonContext.Default);
        var factory = ProgramKitJsonTestComposition.CreateRegistryFactory();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            factory.Create(
                [
                    ProgramKitJsonProfiles.JsonMeta,
                    ProgramKitJsonProfiles.JsonContracts,
                ],
                [replacement],
                []));
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
            exception.Diagnostic.Id);
        Assert.AreEqual("/profileOwnedMetadata", exception.Diagnostic.Path);
    }

    [TestMethod]
    public void PublicFactoryRejectsEveryDefaultImmutableArrayWithOwnedDiagnostics()
    {
        var factory = ProgramKitJsonTestComposition.CreateRegistryFactory();

        var profilesException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            factory.Create(default, [], []));
        var mechanicsException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            factory.Create([], default, []));
        var selectionsException = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            factory.Create([], [], default));

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            profilesException.Diagnostic.Id);
        Assert.AreEqual("/profiles", profilesException.Diagnostic.Path);
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidProfile,
            mechanicsException.Diagnostic.Id);
        Assert.AreEqual(
            "/profileOwnedMetadata",
            mechanicsException.Diagnostic.Path);
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            selectionsException.Diagnostic.Id);
        Assert.AreEqual("/selections", selectionsException.Diagnostic.Path);
    }

    [TestMethod]
    public void ContributedContextCannotReturnForeignOriginMetadata()
    {
        var inner = ForeignOriginSourceJsonContext.Default;
        var context = ForeignOriginContextEmitter.Create(inner);
        Assert.AreSame(context, context.Options.TypeInfoResolver);
        var foreignTypeInfo = context.GetTypeInfo(typeof(string));
        Assert.IsNotNull(foreignTypeInfo);
        Assert.AreSame(inner, foreignTypeInfo.OriginatingResolver);

        var contribution = new JsonTypeInfoResolverContribution(
            Descriptor(
                "foreign-origin-metadata",
                '7',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(string)),
            context);
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            contribution);
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(
            builder.Freeze);
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.Contains(
            "did not originate from the contributed context",
            exception.Diagnostic.Message);
    }

    [TestMethod]
    public async Task ReentrantFreezeFailsPromptlyWithStableDiagnostic()
    {
        IProgramKitJsonBuilder? builder = null;
        var factory = new ReentrantRegistryFactory(
            () => (builder ??
                throw new InvalidOperationException(
                    "The reentrant registry factory has no attached builder."))
                .Freeze());
        builder = new ProgramKitJsonBuilder(factory);

        var freezeTask = Task.Run(builder.Freeze);
        var exception = await Assert.ThrowsExactlyAsync<ProgramKitJsonException>(
            async () =>
            {
                _ = await freezeTask.WaitAsync(
                    TimeSpan.FromSeconds(2),
                    TestContext.CancellationToken);
            });
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.RegistryFrozen,
            exception.Diagnostic.Id);
    }

    [TestMethod]
    public async Task ConcurrentFreezeCallersWaitForAndShareOneRegistry()
    {
        using var factory = new BlockingRegistryFactory(
            ProgramKitJsonTestComposition.CreateRegistryFactory());
        var builder = new ProgramKitJsonBuilder(factory);
        var firstFreeze = Task.Run(builder.Freeze);
        Assert.IsTrue(factory.WaitUntilEntered(TimeSpan.FromSeconds(2)));

        var secondStarted = new TaskCompletionSource(
            TaskCreationOptions.RunContinuationsAsynchronously);
        var secondFreeze = Task.Run(() =>
        {
            secondStarted.SetResult();
            return builder.Freeze();
        });
        await secondStarted.Task.WaitAsync(
            TimeSpan.FromSeconds(2),
            TestContext.CancellationToken);
        await Task.Delay(
            TimeSpan.FromMilliseconds(50),
            TestContext.CancellationToken);
        Assert.IsFalse(secondFreeze.IsCompleted);

        factory.Release();
        var firstRegistry = await firstFreeze.WaitAsync(
            TimeSpan.FromSeconds(2),
            TestContext.CancellationToken);
        var secondRegistry = await secondFreeze.WaitAsync(
            TimeSpan.FromSeconds(2),
            TestContext.CancellationToken);
        Assert.AreSame(firstRegistry, secondRegistry);
        Assert.AreEqual(1, factory.CreateCallCount);
    }

    [TestMethod]
    public void ConverterFactoryCanConvertFailureUsesStableDiagnostic()
    {
        var factory = new ThrowingCanConvertFactory();
        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
        {
            _ = new JsonConverterFactoryContribution(
                Descriptor(
                    "throwing-can-convert",
                    '8',
                    JsonSerializationContributionKind.ConverterFactory,
                    ProgramKitJsonProfiles.JsonContracts.Reference,
                    typeof(DeclaredFactoryValue)),
                factory,
                typeof(DeclaredFactoryValue));
        });
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.AreEqual(
            "/descriptor/targetTypeFamilies",
            exception.Diagnostic.Path);
        Assert.IsInstanceOfType<InvalidOperationException>(
            exception.InnerException);
    }

    [TestMethod]
    public void ConverterFactoryCreateFailureUsesStableDiagnostic()
    {
        var metadata = new JsonTypeInfoResolverContribution(
            Descriptor(
                "throwing-create-metadata",
                '9',
                JsonSerializationContributionKind.TypeInfoResolver,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(FactoryBoundaryModel)),
            FactoryBoundaryJsonContext.Default);
        var factory = new ThrowingCreateConverterFactory();
        var factoryContribution = new JsonConverterFactoryContribution(
            Descriptor(
                "throwing-create-converter",
                'a',
                JsonSerializationContributionKind.ConverterFactory,
                ProgramKitJsonProfiles.JsonContracts.Reference,
                typeof(DeclaredFactoryValue)),
            factory,
            typeof(DeclaredFactoryValue));
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            metadata);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            factoryContribution);
        var registry = builder.Freeze();

        var exception = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
        {
            _ = registry.GetTypeInfo<FactoryBoundaryModel>(
                ProgramKitJsonProfiles.JsonContracts.Reference);
        });
        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            exception.Diagnostic.Id);
        Assert.AreEqual("/targetTypeFamilies", exception.Diagnostic.Path);
        Assert.IsInstanceOfType<InvalidOperationException>(
            exception.InnerException);
    }

    private static JsonSerializationProfile CreateProfile(string name, JsonProfileExtensibility extensibility, char digestMarker) => new(new JsonSerializationProfileRef(new ProgramKitIdentifier(string.Concat("pkid:profile:tests:", name)), new SemanticVersion("1.0.0"), Digest(digestMarker)), ProgramKitJsonProfiles.CanonicalJsonRfc8785, extensibility, ProgramKitJsonProfiles.JsonContracts.Rules, JsonSerializationLimits.Default);
    private static JsonSerializationContributionDescriptor Descriptor(string name, char digestMarker, JsonSerializationContributionKind kind, JsonSerializationProfileRef profile, params Type[] targets) => Descriptor(new ProgramKitIdentifier(string.Concat("pkid:json-contribution:tests:", name)), digestMarker, kind, profile, [], [], targets);
    private static JsonSerializationContributionDescriptor Descriptor(ProgramKitIdentifier identity, char digestMarker, JsonSerializationContributionKind kind, JsonSerializationProfileRef profile, ImmutableArray<ProgramKitIdentifier> before, ImmutableArray<ProgramKitIdentifier> after, params Type[] targets) => new(new JsonSerializationContributionRef(identity, new SemanticVersion("1.0.0"), Digest(digestMarker)), TestPackage, profile.Identity, new SemanticVersionRange("[1.0.0]"), kind, targets.Select(JsonTargetTypeClaim.For).ToImmutableArray(), before, after);
    private static Sha256Digest Digest(char marker) => new(string.Concat("sha256:", new string(marker, 64)));
}
