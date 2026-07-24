using System.Text;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Documentation.Api;

[TestClass]
public sealed class OpenApiDocumentWriterTests
{
    [TestMethod]
    public void ConsumerOwnedContractSetsProjectAsTypedContentWithoutOwningTheirSemantics()
    {
        var shell = DotNetTestContractFactory.Shell();
        var document = DotNetTestContractFactory.ApiDocument(shell);
        var operation = document.Operations[0];
        var continuationUnion = DotNetTestContractFactory.Ref(
            "schema",
            "terminal-result-or-continuation",
            '8');
        var continuationOperation = DotNetTestContractFactory.Ref(
            "operation",
            "continue-exact",
            '9');
        document = document with
        {
            Operations =
            [
                operation with
                {
                    ResultSchemaRevisions = [continuationUnion],
                    RelatedOperationRevisions = [continuationOperation],
                },
            ],
        };
        OpenApiDocumentWriter sut = new(new ProgramKitJsonCanonicalizer());

        var json = Encoding.UTF8.GetString(sut.Write(document).Span);

        Assert.Contains("\"requestBody\"", json);
        Assert.Contains("\"content\":{\"application/json\"", json);
        Assert.Contains("\"oneOf\"", json);
        Assert.Contains(
            string.Concat(
                continuationUnion.Identity.Value,
                "@",
                continuationUnion.Version.Value,
                "#",
                continuationUnion.Digest.Value),
            json);
        Assert.Contains(
            string.Concat(
                continuationOperation.Identity.Value,
                "@",
                continuationOperation.Version.Value,
                "#",
                continuationOperation.Digest.Value),
            json);
        Assert.DoesNotContain("SemanticImage", json);
        Assert.DoesNotContain("\"continuationKind\"", json);
    }

}
