using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Operations.Contracts.Validation;

namespace Orbyss.ProgramKit.OperationsConsumerFixture.Composition;

/// <summary>Isolated package-only composition proving the Operations surface.</summary>
public static class OperationsConsumer
{
    /// <summary>Composes and validates one operation and terminal result.</summary>
    public static bool Validate()
    {
        var schema = Reference("schema", "result", '1');
        var operation = Reference("operation", "inspect", '2');
        var descriptor = new OperationContractDescriptor(
            operation,
            [],
            [new OperationResultContract(schema, OperationResultDisposition.Terminal)],
            [],
            [],
            [],
            null,
            null,
            OperationExpectedRevisionPolicy.Unsupported,
            OperationIdempotencyPolicy.Unsupported,
            OperationCancellationPolicy.Unsupported,
            OperationProgressPolicy.Unsupported,
            new ArtifactCompatibility(
                new ProgramKitIdentifier("pkid:policy:operations-consumer:compatibility"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.WireRead,
                        CompatibilityClassification.Unknown,
                        []),
                ],
                new SemanticVersionRange("[1.0.0]"),
                new SemanticVersionRange("[1.0.0]"),
                []),
            new OperationDeprecation(false, null));
        var catalog = new OperationContractCatalog([descriptor]);
        var result = new OperationResultDocument(
            "invocation-1",
            operation,
            schema,
            Reference("document", "result", '3'),
            OperationResultDisposition.Terminal,
            [],
            null);

        OperationContractCatalogValidator catalogValidator = new();
        OperationResultDocumentValidator resultValidator = new(catalog);
        return catalogValidator.Validate(catalog).IsValid &&
               resultValidator.Validate(result).IsValid;
    }

    private static ArtifactReference Reference(string kind, string name, char digest) =>
        new(
            new ProgramKitIdentifier(
                string.Concat("pkid:", kind, ":operations-consumer:", name)),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                string.Concat("sha256:", new string(digest, 64))));
}
