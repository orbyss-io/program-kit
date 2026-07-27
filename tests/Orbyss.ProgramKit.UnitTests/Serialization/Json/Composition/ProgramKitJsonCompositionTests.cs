using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

[TestClass]
public sealed class ProgramKitJsonCompositionTests
{
    private static readonly string[] ExpectedContributionOrder =
    [
        "pkid:json-contribution:tests:alpha",
        "pkid:json-contribution:tests:zulu",
    ];

    [TestMethod]
    public void ContributionOrderUsesStableIdentityTieBreak()
    {
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonContributionTestFactory.CreateResolverContribution(
                "zulu",
                "1",
                typeof(FactoryModel)));
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "2",
                typeof(ProbeModel)));

        var selection = builder
            .Freeze()
            .Selections
            .Single(item =>
                item.Profile ==
                ProgramKitJsonProfiles.JsonContracts.Reference);

        Assert.AreSequenceEqual(
            ExpectedContributionOrder,
            selection.Contributions
                .Select(static item => item.Identity.Value)
                .ToArray());
    }

    [TestMethod]
    public void RegistryRejectsConflictGapCycleAndChangedRevisionBytes()
    {
        AssertCompositionFailure(
            ProgramKitJsonDiagnosticIds.ContributionConflict,
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "1"),
            JsonContributionTestFactory.CreateResolverContribution(
                "beta",
                "2"));
        AssertCompositionFailure(
            ProgramKitJsonDiagnosticIds.OrderingGap,
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "1",
                before:
                [
                    new ProgramKitIdentifier(
                        "pkid:json-contribution:tests:missing"),
                ]));
        AssertCompositionFailure(
            ProgramKitJsonDiagnosticIds.OrderingCycle,
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "1",
                typeof(ProbeModel),
                before:
                [
                    new ProgramKitIdentifier(
                        "pkid:json-contribution:tests:beta"),
                ]),
            JsonContributionTestFactory.CreateResolverContribution(
                "beta",
                "2",
                typeof(FactoryModel),
                before:
                [
                    new ProgramKitIdentifier(
                        "pkid:json-contribution:tests:alpha"),
                ]));
        AssertCompositionFailure(
            ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "1"),
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "2"));
        AssertCompositionFailure(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            JsonContributionTestFactory.CreateResolverContribution(
                "duplicate",
                "3"),
            JsonContributionTestFactory.CreateResolverContribution(
                "duplicate",
                "3"));
    }

    [TestMethod]
    public void ExplicitPrecedenceResolvesACompetingTargetClaim()
    {
        var alpha =
            JsonContributionTestFactory.CreateResolverContribution(
                "alpha",
                "1",
                typeof(ProbeModel),
                before:
                [
                    new ProgramKitIdentifier(
                        "pkid:json-contribution:tests:beta"),
                ]);
        var beta =
            JsonContributionTestFactory.CreateResolverContribution(
                "beta",
                "2");
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            beta);
        builder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonContracts.Reference,
            alpha);

        var selection = builder
            .Freeze()
            .Selections
            .Single(item =>
                item.Profile ==
                ProgramKitJsonProfiles.JsonContracts.Reference);

        Assert.AreEqual(
            alpha.Descriptor.Reference,
            selection.Contributions[0]);
        Assert.AreEqual(
            beta.Descriptor.Reference,
            selection.Contributions[1]);
    }

    [TestMethod]
    public void MetaProfileAndFrozenBuilderRejectMutation()
    {
        var metaContribution = new JsonTypeInfoResolverContribution(
            JsonContributionTestFactory.CreateDescriptor(
                "meta",
                "1",
                JsonSerializationContributionKind.TypeInfoResolver,
                JsonTargetTypeClaim.For<ProbeModel>(),
                applicableProfile:
                    ProgramKitJsonProfiles.JsonMeta.Reference),
            ProbeJsonTestContext.Default);
        var metaBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        metaBuilder.AddJsonSerializationContribution(
            ProgramKitJsonProfiles.JsonMeta.Reference,
            metaContribution);

        var metaException =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                metaBuilder.Freeze);

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.NonExtensibleProfile,
            metaException.Diagnostic.Id);

        var frozenBuilder = ProgramKitJsonTestComposition.CreateBuilder();
        _ = frozenBuilder.Freeze();

        var frozenException =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                () => frozenBuilder.AddProfile(
                    ProgramKitJsonProfiles.JsonContracts));

        Assert.AreEqual(
            ProgramKitJsonDiagnosticIds.RegistryFrozen,
            frozenException.Diagnostic.Id);
    }

    [TestMethod]
    public void ServiceCollectionCreatesOneShellScopedBuilder()
    {
        var services = new ServiceCollection();

        var first = services.AddProgramKitJson();
        var second = services.AddProgramKitJson();

        Assert.AreSame(first, second);
        Assert.HasCount(6, services);
        Assert.ContainsSingle(
            services.Where(static descriptor =>
                descriptor.ServiceType ==
                typeof(IProgramKitJsonBuilder)));
        Assert.DoesNotContain(
            static descriptor =>
                descriptor.ServiceType == typeof(ProgramKitJsonBuilder),
            services);
        Assert.AreEqual(
            typeof(IProgramKitJsonBuilder),
            typeof(ProgramKitJsonServiceCollectionExtensions)
                .GetMethod(
                    nameof(
                        ProgramKitJsonServiceCollectionExtensions
                            .AddProgramKitJson))!
                .ReturnType);
        Assert.Contains(
            static descriptor =>
                descriptor.ServiceType ==
                typeof(IProgramKitJsonSerializer),
            services);
        Assert.Contains(
            static descriptor =>
                descriptor.ServiceType ==
                typeof(IProgramKitJsonCanonicalizer),
            services);
    }

    [TestMethod]
    [DataRow("instance")]
    [DataRow("type")]
    [DataRow("factory")]
    public void ServiceCollectionRejectsForeignBuilderRegistrations(
        string registrationKind)
    {
        var services = new ServiceCollection();
        switch (registrationKind)
        {
            case "instance":
                services.AddSingleton<IProgramKitJsonBuilder>(
                    new StubProgramKitJsonBuilder());
                break;
            case "type":
                services.AddSingleton<
                    IProgramKitJsonBuilder,
                    StubProgramKitJsonBuilder>();
                break;
            case "factory":
                services.AddSingleton<IProgramKitJsonBuilder>(
                    static _ => new StubProgramKitJsonBuilder());
                break;
            default:
                throw new ArgumentOutOfRangeException(
                    nameof(registrationKind),
                    registrationKind,
                    "Unknown service-registration fixture.");
        }

        var exception = Assert.ThrowsExactly<InvalidOperationException>(
            services.AddProgramKitJson);

        Assert.Contains("foreign Program Kit JSON", exception.Message);
        Assert.ContainsSingle(
            services.Where(static descriptor =>
                descriptor.ServiceType == typeof(IProgramKitJsonBuilder)));
        Assert.DoesNotContain(
            static descriptor =>
                descriptor.ServiceType == typeof(IProgramKitJsonSerializer),
            services);
    }

    [TestMethod]
    public void ServiceCollectionRejectsFullyMimickedForeignRegistryDelegate()
    {
        var services = new ServiceCollection();
        _ = services.AddProgramKitJson();
        var ownedRegistryDescriptor = services.Single(static descriptor =>
            descriptor.ServiceType == typeof(IProgramKitJsonRegistry));
        Assert.IsTrue(services.Remove(ownedRegistryDescriptor));
        services.AddSingleton<IProgramKitJsonRegistry>(static provider =>
            provider.GetRequiredService<IProgramKitJsonBuilder>().Freeze());

        var exception = Assert.ThrowsExactly<InvalidOperationException>(
            services.AddProgramKitJson);

        Assert.Contains("foreign Program Kit JSON", exception.Message);
        Assert.HasCount(6, services);
        Assert.HasCount(
            5,
            services.Where(static descriptor =>
                descriptor.ServiceType == typeof(IProgramKitJsonRegistryFactory) ||
                descriptor.ServiceType == typeof(IProgramKitJsonBuilder) ||
                descriptor.ServiceType == typeof(IProgramKitJsonRegistry) ||
                descriptor.ServiceType == typeof(IProgramKitJsonCanonicalizer) ||
                descriptor.ServiceType == typeof(IProgramKitJsonSerializer)));
    }

    [TestMethod]
    [DataRow("registry-factory")]
    [DataRow("builder")]
    [DataRow("registry")]
    [DataRow("canonicalizer")]
    [DataRow("serializer")]
    [DataRow("ownership-marker")]
    public void ServiceCollectionRejectsForeignReplacementInEveryOwnedSlot(
        string serviceSlot)
    {
        var services = new ServiceCollection();
        _ = services.AddProgramKitJson();
        var serviceType = serviceSlot switch
        {
            "registry-factory" => typeof(IProgramKitJsonRegistryFactory),
            "builder" => typeof(IProgramKitJsonBuilder),
            "registry" => typeof(IProgramKitJsonRegistry),
            "canonicalizer" => typeof(IProgramKitJsonCanonicalizer),
            "serializer" => typeof(IProgramKitJsonSerializer),
            "ownership-marker" => services.Single(static descriptor =>
                descriptor.ServiceType !=
                    typeof(IProgramKitJsonRegistryFactory) &&
                descriptor.ServiceType != typeof(IProgramKitJsonBuilder) &&
                descriptor.ServiceType != typeof(IProgramKitJsonRegistry) &&
                descriptor.ServiceType !=
                    typeof(IProgramKitJsonCanonicalizer) &&
                descriptor.ServiceType !=
                    typeof(IProgramKitJsonSerializer)).ServiceType,
            _ => throw new ArgumentOutOfRangeException(
                nameof(serviceSlot),
                serviceSlot,
                "Unknown Program Kit JSON service slot."),
        };
        var ownedDescriptor = services.Single(descriptor =>
            descriptor.ServiceType == serviceType);
        Assert.IsTrue(services.Remove(ownedDescriptor));
        switch (serviceSlot)
        {
            case "registry-factory":
                services.AddSingleton<IProgramKitJsonRegistryFactory>(
                    new StubProgramKitJsonRegistryFactory(
                        new StubProgramKitJsonRegistry()));
                break;
            case "builder":
                services.AddSingleton<IProgramKitJsonBuilder>(
                    ProgramKitJsonTestComposition.CreateBuilder());
                break;
            case "registry":
                services.AddSingleton<IProgramKitJsonRegistry>(
                    static provider =>
                        provider
                            .GetRequiredService<IProgramKitJsonBuilder>()
                            .Freeze());
                break;
            case "canonicalizer":
                services.AddSingleton<IProgramKitJsonCanonicalizer>(
                    new ProgramKitJsonCanonicalizer());
                break;
            case "serializer":
                services.AddSingleton<IProgramKitJsonSerializer>(
                    static _ => throw new NotSupportedException(
                        "A foreign serializer factory must not be invoked."));
                break;
            case "ownership-marker":
                services.AddSingleton(
                    serviceType,
                    static _ => new object());
                break;
        }

        var exception = Assert.ThrowsExactly<InvalidOperationException>(
            services.AddProgramKitJson);

        Assert.Contains("foreign Program Kit JSON", exception.Message);
        Assert.HasCount(6, services);
        Assert.HasCount(
            5,
            services.Where(static descriptor =>
                descriptor.ServiceType == typeof(IProgramKitJsonRegistryFactory) ||
                descriptor.ServiceType == typeof(IProgramKitJsonBuilder) ||
                descriptor.ServiceType == typeof(IProgramKitJsonRegistry) ||
                descriptor.ServiceType == typeof(IProgramKitJsonCanonicalizer) ||
                descriptor.ServiceType == typeof(IProgramKitJsonSerializer)));
    }

    private static void AssertCompositionFailure(
        string diagnosticId,
        params JsonSerializationContribution[] contributions)
    {
        var builder = ProgramKitJsonTestComposition.CreateBuilder();
        foreach (var contribution in contributions)
        {
            builder.AddJsonSerializationContribution(
                ProgramKitJsonProfiles.JsonContracts.Reference,
                contribution);
        }

        var exception =
            Assert.ThrowsExactly<ProgramKitJsonException>(
                builder.Freeze);
        Assert.AreEqual(diagnosticId, exception.Diagnostic.Id);
    }
}
