using Orbyss.ProgramKit.UnitTests.Workbench.Composition.Extensions.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Composition.Extensions;

[TestClass]
public sealed class WorkbenchExtensionRegistryFactoryTests
{
    [TestMethod]
    public void CreateRejectsDuplicatesBeforeRegistrationsCanCollapse()
    {
        var descriptor = Descriptor(TestContractValues.Digest);
        IWorkbenchExtension<string, string> first =
            new TestWorkbenchExtension(descriptor);
        IWorkbenchExtension<string, string> duplicate =
            new TestWorkbenchExtension(descriptor);
        WorkbenchExtensionRegistryFactory sut = new();

        var result = sut.Create(new[] { first, duplicate });

        Assert.IsFalse(result.IsSuccessful);
        Assert.IsTrue(result.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.InvalidExtensionSelection));
    }

    [TestMethod]
    public void CreateRejectsConflictingDigestsForOneSemanticRevision()
    {
        IWorkbenchExtension<string, string> first =
            new TestWorkbenchExtension(Descriptor(TestContractValues.Digest));
        var alternate = Sha256Digest.Parse(
            string.Concat("sha256:", new string('b', 64)));
        IWorkbenchExtension<string, string> conflicting =
            new TestWorkbenchExtension(Descriptor(alternate));
        WorkbenchExtensionRegistryFactory sut = new();

        var result = sut.Create(new[] { first, conflicting });

        Assert.IsFalse(result.IsSuccessful);
        Assert.IsTrue(result.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.InvalidExtensionSelection));
    }

    private static WorkbenchExtensionDescriptor Descriptor(Sha256Digest digest) =>
        new(
            ProgramKitIdentifier.Parse("pkid:extension:program-kit:test"),
            SemanticVersion.Parse("1.0.0"),
            digest);
}
