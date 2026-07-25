using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;
using Orbyss.ProgramKit.Operations.Contracts.Validation;

namespace Orbyss.ProgramKit.UnitTests.Operations.Contracts;

[TestClass]
public sealed class OperationContractTests
{
    [TestMethod]
    public void ExplicitClosedCatalogAndInvocationDocumentsValidate()
    {
        var catalog = Catalog();
        var descriptor = catalog.Operations[0];
        var request = new OperationInvocationDocument(
            "invocation-1",
            descriptor.OperationRevision,
            descriptor.RequestContractRevisions[0],
            Ref("document", "request", '8'),
            "correlation-1",
            null,
            "cancel-1",
            null,
            "idempotency-1");

        OperationContractCatalogValidator catalogValidator = new();
        OperationInvocationDocumentValidator invocationValidator = new(catalog);
        var catalogValidation = catalogValidator.Validate(catalog);
        var invocationValidation = invocationValidator.Validate(request);

        Assert.IsTrue(catalogValidation.IsValid, Format(catalogValidation));
        Assert.IsTrue(invocationValidation.IsValid, Format(invocationValidation));
    }

    [TestMethod]
    public void CatalogRejectsConflictingAndOpenRelatedOperationRegistrations()
    {
        var catalog = Catalog();
        var first = catalog.Operations[0];
        var conflicting = first with
        {
            OperationRevision = first.OperationRevision with
            {
                Version = new SemanticVersion("2.0.0"),
                Digest = Digest('9'),
            },
        };
        var open = first with
        {
            RelatedOperations =
            [
                new RelatedOperationContract(
                    Id("relation", "missing"),
                    Ref("operation", "missing", 'a'),
                    first.RequestContractRevisions[0]),
            ],
        };

        OperationContractCatalogValidator validator = new();
        var validation = validator.Validate(
            new OperationContractCatalog([open, conflicting]));

        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == OperationsDiagnosticIds.ConflictingRegistration));
        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == OperationsDiagnosticIds.CatalogClosureFailure));
    }

    [TestMethod]
    public void ResultAndProgressValidationPreserveMechanicalBoundaries()
    {
        var catalog = Catalog();
        var descriptor = catalog.Operations[0];
        var terminalContract = descriptor.ResultContracts.Single(result =>
            result.Disposition == OperationResultDisposition.Terminal);
        var progress = new OperationProgressDocument(
            "invocation-1",
            descriptor.OperationRevision,
            0,
            descriptor.ProgressContractRevisions[0],
            Ref("document", "progress", 'b'));
        var result = new OperationResultDocument(
            "invocation-1",
            descriptor.OperationRevision,
            terminalContract.ContractRevision,
            Ref("document", "result", 'c'),
            OperationResultDisposition.Terminal,
            [
                new OperationDiagnosticDocument(
                    descriptor.DiagnosticContractRevisions[0],
                    Ref("document", "diagnostic", 'd')),
            ],
            null);

        OperationProgressDocumentValidator progressValidator = new(catalog);
        OperationResultDocumentValidator resultValidator = new(catalog);
        var progressValidation = progressValidator.Validate(progress);
        var resultValidation = resultValidator.Validate(result);

        Assert.IsTrue(progressValidation.IsValid, Format(progressValidation));
        Assert.IsTrue(resultValidation.IsValid, Format(resultValidation));
    }

    [TestMethod]
    public void AdditionalInputRequiresAnExactDeclaredRelatedOperation()
    {
        var catalog = Catalog();
        var descriptor = catalog.Operations[0];
        var additionalInput = descriptor.ResultContracts.Single(result =>
            result.Disposition == OperationResultDisposition.AdditionalInputRequired);
        var invalid = new OperationResultDocument(
            "invocation-1",
            descriptor.OperationRevision,
            additionalInput.ContractRevision,
            Ref("document", "result", 'e'),
            OperationResultDisposition.AdditionalInputRequired,
            [],
            Ref("operation", "unknown", 'f'));

        OperationResultDocumentValidator validator = new(catalog);
        var validation = validator.Validate(invalid);

        Assert.IsTrue(validation.Diagnostics.Any(diagnostic =>
            diagnostic.Id == OperationsDiagnosticIds.InvalidResult));
    }

    private static OperationContractCatalog Catalog()
    {
        var request = Ref("schema", "request", '1');
        var continuationRequest = Ref("schema", "continuation-request", '2');
        var continuation = Descriptor(
            Ref("operation", "continue", '3'),
            [continuationRequest],
            [],
            OperationProgressPolicy.Unsupported,
            []);
        var operation = Descriptor(
            Ref("operation", "run", '4'),
            [request],
            [
                new RelatedOperationContract(
                    Id("relation", "additional-input"),
                    continuation.OperationRevision,
                    continuationRequest),
            ],
            OperationProgressPolicy.BoundedNonAuthoritative,
            [Ref("schema", "progress", '5')]);
        return new OperationContractCatalog([operation, continuation]);
    }

    private static OperationContractDescriptor Descriptor(
        ArtifactReference operation,
        ImmutableArray<ArtifactReference> requests,
        ImmutableArray<RelatedOperationContract> related,
        OperationProgressPolicy progressPolicy,
        ImmutableArray<ArtifactReference> progress) =>
        new(
            operation,
            requests,
            [
                new OperationResultContract(
                    Ref("schema", string.Concat(operation.Identity.Name, "-result"), '6'),
                    OperationResultDisposition.Terminal),
                new OperationResultContract(
                    Ref("schema", string.Concat(operation.Identity.Name, "-input"), '7'),
                    OperationResultDisposition.AdditionalInputRequired),
            ],
            [Ref("schema", "diagnostic", '8')],
            progress,
            related,
            null,
            null,
            OperationExpectedRevisionPolicy.Unsupported,
            OperationIdempotencyPolicy.Required,
            OperationCancellationPolicy.Cooperative,
            progressPolicy,
            Compatibility(),
            new OperationDeprecation(false, null));

    private static ArtifactCompatibility Compatibility() =>
        new(
            Id("policy", "compatibility"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            new SemanticVersionRange("[1.0.0]"),
            new SemanticVersionRange("[1.0.0]"),
            []);

    private static ArtifactReference Ref(string kind, string name, char digest) =>
        new(Id(kind, name), new SemanticVersion("1.0.0"), Digest(digest));

    private static ProgramKitIdentifier Id(string kind, string name) =>
        new(string.Concat("pkid:", kind, ":operations-test:", name));

    private static Sha256Digest Digest(char value) =>
        new(string.Concat("sha256:", new string(value, 64)));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                string.Concat(diagnostic.Id, " ", diagnostic.Path, ": ", diagnostic.Message)));
}
