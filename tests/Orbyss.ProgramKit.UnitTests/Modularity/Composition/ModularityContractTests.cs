namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

[TestClass]
public sealed class ModularityContractTests
{
    [TestMethod]
    public void ContributionRegistryFreezesExplicitTopologicalOrder()
    {
        var second = Descriptor("second", priority: -100);
        var first = Descriptor(
            "first",
            priority: 100,
            before: [second.Registration.Identity]);
        var registry =
            ModularityTestComposition.CreateDomainContributionRegistry(
        [
            Registration(second),
            Registration(first),
        ]);

        var ordered = registry.GetRegistrations<RecordedContribution>();

        Assert.HasCount(2, ordered);
        Assert.AreEqual(
            first.Registration.Identity,
            ordered[0].Descriptor.Registration.Identity);
        Assert.AreEqual(
            second.Registration.Identity,
            ordered[1].Descriptor.Registration.Identity);
        Assert.ThrowsExactly<NotSupportedException>(() =>
            ((IList<DomainContributionHandlerRegistration>)ordered).Add(
                Registration(Descriptor("third"))));
    }

    [TestMethod]
    public void ContributionRegistrationHierarchyCannotBeExtendedByConsumers()
    {
        var externallyUsableConstructors =
            typeof(DomainContributionHandlerRegistration)
                .GetConstructors(
                    System.Reflection.BindingFlags.Instance |
                    System.Reflection.BindingFlags.Public |
                    System.Reflection.BindingFlags.NonPublic)
                .Where(static constructor =>
                    constructor.IsPublic ||
                    constructor.IsFamily ||
                    constructor.IsFamilyOrAssembly)
                .ToArray();

        Assert.IsEmpty(externallyUsableConstructors);
        Assert.IsTrue(
            typeof(TypedDomainContributionHandlerRegistration<>).IsSealed);
    }

    [TestMethod]
    public void DuplicateMissingAndCyclicRegistrationsFailComposition()
    {
        var duplicate = Descriptor("duplicate");
        var duplicateException = Assert.ThrowsExactly<ModularityValidationException>(() =>
            ModularityTestComposition.CreateDomainContributionRegistry(
            [
                Registration(duplicate),
                Registration(duplicate),
            ]));

        var missingException = Assert.ThrowsExactly<ModularityValidationException>(() =>
            ModularityTestComposition.CreateDomainContributionRegistry(
            [
                Registration(Descriptor(
                    "missing-owner",
                    before:
                    [
                        ProgramKitIdentifier.Parse(
                            "pkid:contribution:program-kit:not-registered"),
                    ])),
            ]));

        var leftIdentity =
            ProgramKitIdentifier.Parse("pkid:contribution:program-kit:left");
        var rightIdentity =
            ProgramKitIdentifier.Parse("pkid:contribution:program-kit:right");
        var cycleException = Assert.ThrowsExactly<ModularityValidationException>(() =>
            ModularityTestComposition.CreateDomainContributionRegistry(
            [
                Registration(Descriptor("left", before: [rightIdentity])),
                Registration(Descriptor("right", before: [leftIdentity])),
            ]));

        Assert.IsTrue(duplicateException.Validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.DuplicateRegistrationIdentity));
        Assert.IsTrue(missingException.Validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.MissingOrderingDependency));
        Assert.IsTrue(cycleException.Validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.OrderingCycle));
    }

    [TestMethod]
    public void InvalidContributionTypesAndOrderingDescriptorsFailClosed()
    {
        var invalidType = Assert.ThrowsExactly<ModularityValidationException>(() =>
            ModularityTestComposition.CreateDomainContributionRegistry(
            [
                new TypedDomainContributionHandlerRegistration<IDomainContribution>(
                    Descriptor("invalid-type"),
                    new NoOpInterfaceHandler()),
            ]));
        var invalidOrder = Assert.ThrowsExactly<ModularityValidationException>(() =>
            ModularityTestComposition.CreateDomainContributionRegistry(
            [
                Registration(new ModularityRegistrationDescriptor(
                    Reference("invalid-order"),
                    ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
                    new ModularityOrderDescriptor(0, default, []))),
            ]));

        Assert.IsTrue(invalidType.Validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.InvalidRegistrationType));
        Assert.IsTrue(invalidOrder.Validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ModularityDiagnosticIds.InvalidOrderingDescriptor));
    }

    [TestMethod]
    public void DiagnosticCatalogPublishesOnlyCanonicalStableIds()
    {
        Assert.HasCount(
            ModularityDiagnosticIds.All.Length,
            ModularityDiagnosticCatalog.Definitions);
        Assert.HasCount(
            ModularityDiagnosticIds.All.Length,
            ModularityDiagnosticIds.All.Distinct(StringComparer.Ordinal));
        Assert.IsTrue(ModularityDiagnosticIds.All.All(identifier =>
            identifier.StartsWith("PKMOD", StringComparison.Ordinal)));
        Assert.AreSequenceEqual(
            ModularityDiagnosticIds.All,
            ModularityDiagnosticCatalog.Definitions
                .Select(static definition => definition.Id));
    }

    private static TypedDomainContributionHandlerRegistration<RecordedContribution>
        Registration(ModularityRegistrationDescriptor descriptor) =>
        new(descriptor, new NoOpHandler());

    private static ModularityRegistrationDescriptor Descriptor(
        string name,
        int priority = 0,
        ProgramKitIdentifier[]? before = null,
        ProgramKitIdentifier[]? after = null) =>
        new(
            Reference(name),
            ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
            new ModularityOrderDescriptor(
                priority,
                before is null ? [] : [.. before],
                after is null ? [] : [.. after]));

    private static ArtifactReference Reference(string name) =>
        new(
            ProgramKitIdentifier.Parse(
                string.Concat("pkid:contribution:program-kit:", name)),
            SemanticVersion.Parse("1.0.0"),
            Sha256Digest.Parse(
                string.Concat("sha256:", new string('a', 64))));

}
