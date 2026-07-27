using System.Globalization;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Rendering;

[TestClass]
public sealed class StructuralPatternCatalogMarkdownRendererTests
{
    [TestMethod]
    public void RenderPreservesRevisableGuidanceAndIsCultureInvariant()
    {
        var catalog = new StructuralPatternCatalog(
            ProgramKitIdentifier.Parse(
                "pkid:catalog:program-kit:structural-patterns"),
            SemanticVersion.Parse("1.0.0"),
            "Reusable structural guidance",
            [
                new StructuralPatternDefinition(
                    ProgramKitIdentifier.Parse(
                        "pkid:pattern:program-kit:provider-adapter"),
                    "Provider adapter",
                    "Keep consumer policy above provider contracts.",
                    ["A provider contract is selected explicitly."],
                    ["Adds one translation boundary."],
                    [
                        new StructuralPatternExample(
                            "Consumer policy",
                            "A consumer owns terminal result semantics.",
                            "An adapter projects the provider contract into the consumer shape.",
                            "Provider meaning remains outside the consumer domain."),
                    ],
                    ["Reject ownership inversion in the dependency graph."],
                    ["Review whether an adapter adds real consumer meaning."]),
            ]);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        IProgramKitSemanticValidator<StructuralPatternCatalog> validator =
            new StructuralPatternCatalogValidator(envelopeValidator);
        StructuralPatternCatalogMarkdownRenderer renderer =
            new StructuralPatternCatalogMarkdownRenderer(validator);
        var originalCulture = CultureInfo.CurrentCulture;
        var originalUiCulture = CultureInfo.CurrentUICulture;
        try
        {
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("tr-TR");
            CultureInfo.CurrentUICulture = CultureInfo.GetCultureInfo("tr-TR");
            var first = renderer.RenderMarkdown(catalog);
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("ar-SA");
            CultureInfo.CurrentUICulture = CultureInfo.GetCultureInfo("ar-SA");
            var second = renderer.RenderMarkdown(catalog);

            Assert.AreEqual(first, second);
            Assert.Contains("# Reusable structural guidance\n", first);
            Assert.Contains("## Provider adapter\n", first);
            Assert.Contains(
                "- Reject ownership inversion in the dependency graph.\n",
                first);
            Assert.EndsWith(
                "- Review whether an adapter adds real consumer meaning.\n",
                first);
        }
        finally
        {
            CultureInfo.CurrentCulture = originalCulture;
            CultureInfo.CurrentUICulture = originalUiCulture;
        }
    }
}
