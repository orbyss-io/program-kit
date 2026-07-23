using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>Describes one exact JSON Schema resource without imposing a schema-engine dependency.</summary>
/// <param name="SchemaReference">The exact schema identity, version, and source-byte digest.</param>
/// <param name="CanonicalUri">The canonical JSON Schema URI.</param>
/// <param name="ResourceName">The module-owned resource name.</param>
/// <param name="MediaType">The resource media type.</param>
/// <param name="OwnerId">The semantic owner of the raw schema contract.</param>
/// <param name="Status">The truthful implementation status of the schema.</param>
/// <param name="Consumers">Explicit consumers of the schema contract.</param>
/// <param name="Provenance">Producer and exact approved source inputs.</param>
/// <param name="Compatibility">Compatibility policy, ranges, dimensions, and migrations.</param>
/// <remarks>
/// <see cref="ArtifactReference.Digest"/> binds the raw schema source bytes.
/// It is not a claim that a canonical artifact envelope has been constructed;
/// canonical-envelope integrity remains W015 work.
/// </remarks>
public sealed record ProgramKitSchemaResource(
    ArtifactReference SchemaReference,
    Uri CanonicalUri,
    string ResourceName,
    string MediaType,
    ProgramKitIdentifier OwnerId,
    ArtifactStatus Status,
    ImmutableArray<ProgramKitIdentifier> Consumers,
    ArtifactProvenance Provenance,
    ArtifactCompatibility Compatibility);

/// <summary>
/// Supplies explicitly registered schema descriptors and streams to a consumer
/// without coupling contract packages to a schema implementation.
/// </summary>
public interface IProgramKitSchemaModule
{
    /// <summary>Gets the stable module identity.</summary>
    ProgramKitIdentifier Identity { get; }

    /// <summary>Gets the independently versioned module contract.</summary>
    SemanticVersion Version { get; }

    /// <summary>Gets exact schema resources in deterministic registration order.</summary>
    ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    /// <summary>Opens the exact selected schema resource for reading.</summary>
    Stream OpenRead(ArtifactReference schemaReference);
}

/// <summary>Explicit schema module for schemas owned by Orbyss.ProgramKit.Artifacts.</summary>
public sealed class ArtifactsSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Artifacts.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:artifacts");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:workbench"),
        new("pkid:test:program-kit:conformance-tests"),
    ];
    private static readonly ArtifactProvenance SchemaProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:design:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest(
                        "sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9")),
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:plan:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest(
                        "sha256:6d7396d5eb71e0d064231110e2ccfcae2aea838ca851b1420ff310df127cd951")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:artifacts"),
            "pk-w010-approved-review-set-0-3-0");
    private static readonly ArtifactCompatibility SchemaCompatibility =
        new(
            new ProgramKitIdentifier(
                "pkid:contract:program-kit:schema-compatibility-policy"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
                new CompatibilityClaim(
                    CompatibilityDimension.WireWrite,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            ExactSchemaVersion,
            ExactSchemaVersion,
            []);

    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "artifact-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/definitions.schema.json",
            "009a1360b1afcb1d91874d694f18318a91800d38626ca0c7696ce931856598ff"),
        Create(
            "artifact-envelope",
            "artifact-envelope.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/artifact-envelope.schema.json",
            "c2389234562fb5a5e32d8bdc966c9f796ea4da0eeac1a0eb324956ef3f1e8f14"),
        Create(
            "versioned-component-manifest",
            "versioned-component-manifest.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/versioned-component-manifest.schema.json",
            "6962cc487413df4361b873709b88acd6fe18608bd17a470a1b1aa56147197c08"),
        Create(
            "version-map",
            "version-map.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/version-map.schema.json",
            "c2a5145d3142ea9d1b10e313581a210538628861cc08893de76c754164d2f859"),
        Create(
            "version-selection",
            "version-selection.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/version-selection.schema.json",
            "029ea80c946a42218e40b6c4269d3ea08ab165f78de60dc6a0488fba7518faad"),
        Create(
            "migration-definition",
            "migration-definition.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/migration-definition.schema.json",
            "bf7dad73cf4135640b7ac98d7e3fae8236dcd955c7c48e9fdc08a1ae088a3294"),
        Create(
            "migration-assessment",
            "migration-assessment.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/migration-assessment.schema.json",
            "dd72e65ace420da64bd03903bcf0e7bffca53b7a470c20d5beae6f54c0aad2a9"),
        Create(
            "rfc8785-vector-set",
            "rfc8785-vector-set.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/rfc8785-vector-set.schema.json",
            "40b14e5459501ca6256c8e30099fea425fc979e97dbdfc85f121620ff9b9a4af"),
    ];

    private ArtifactsSchemaModule()
    {
    }

    /// <summary>Gets the singleton stateless schema module.</summary>
    public static ArtifactsSchemaModule Instance { get; } = new();

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:artifact-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => SchemaVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => SchemaResources;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var exactKey = ArtifactReferenceValidator.ExactKey(schemaReference);
        var resource = SchemaResources.FirstOrDefault(candidate =>
            string.Equals(
                ArtifactReferenceValidator.ExactKey(candidate.SchemaReference),
                exactKey,
                StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat("The exact schema reference is not registered: ", exactKey));
        }

        return typeof(ArtifactsSchemaModule).Assembly.GetManifestResourceStream(
                   string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat("The registered schema resource is unavailable: ", resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest)
    {
        return new ProgramKitSchemaResource(
            new ArtifactReference(
                new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
                SchemaVersion,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            SchemaOwner,
            ArtifactStatus.Implemented,
            SchemaConsumers,
            SchemaProvenance,
            SchemaCompatibility);
    }
}

/// <summary>Validates schema-module descriptors without opening resources or performing I/O.</summary>
public sealed class ProgramKitSchemaModuleValidator :
    IProgramKitSemanticValidator<IProgramKitSchemaModule>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(IProgramKitSchemaModule value)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "A schema module is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, "/identity"));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, "/version"));
        if (value.Resources.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "A schema module must register at least one resource.",
                "/resources");
            return diagnostics.ToResult();
        }

        var references = new HashSet<string>(StringComparer.Ordinal);
        var uris = new HashSet<string>(StringComparer.Ordinal);
        var names = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Resources.Length; index++)
        {
            var resource = value.Resources[index];
            var path = string.Concat("/resources/", index);
            if (resource is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "A schema resource descriptor is required.",
                    path);
                continue;
            }

            diagnostics.Add(ArtifactReferenceValidator.Validate(
                resource.SchemaReference,
                ArtifactReferenceValidator.Path(path, "schemaReference")));
            if (resource.SchemaReference is not null &&
                !string.Equals(resource.SchemaReference.Identity.Kind, "schema", StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "A schema resource reference must have PKID kind 'schema'.",
                    ArtifactReferenceValidator.Path(path, "schemaReference/identity"));
            }

            if (resource.CanonicalUri is null ||
                !resource.CanonicalUri.IsAbsoluteUri ||
                !string.Equals(resource.CanonicalUri.Scheme, Uri.UriSchemeHttps, StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Canonical schema URI must be an absolute HTTPS URI.",
                    ArtifactReferenceValidator.Path(path, "canonicalUri"));
            }

            if (string.IsNullOrWhiteSpace(resource.ResourceName) ||
                resource.ResourceName.Contains("..", StringComparison.Ordinal) ||
                resource.ResourceName.Contains('/') ||
                resource.ResourceName.Contains('\\'))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Resource name must be a non-empty, non-traversing module-local name.",
                    ArtifactReferenceValidator.Path(path, "resourceName"));
            }

            if (!string.Equals(resource.MediaType, "application/schema+json", StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Schema resource media type must be 'application/schema+json'.",
                    ArtifactReferenceValidator.Path(path, "mediaType"));
            }

            ValidateSidecar(resource, path, diagnostics);

            if (resource.SchemaReference is not null &&
                !references.Add(ArtifactReferenceValidator.ExactKey(resource.SchemaReference)))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Exact schema references must be unique.",
                    ArtifactReferenceValidator.Path(path, "schemaReference"));
            }

            if (resource.CanonicalUri is not null &&
                !uris.Add(resource.CanonicalUri.AbsoluteUri))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Canonical schema URIs must be unique.",
                    ArtifactReferenceValidator.Path(path, "canonicalUri"));
            }

            if (!names.Add(resource.ResourceName))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    "Schema resource names must be unique.",
                    ArtifactReferenceValidator.Path(path, "resourceName"));
            }
        }

        return diagnostics.ToResult();
    }

    private static void ValidateSidecar(
        ProgramKitSchemaResource resource,
        string path,
        ArtifactDiagnosticBuilder diagnostics)
    {
        diagnostics.Add(ProgramKitIdentifier.Validate(
            resource.OwnerId.Value,
            ArtifactReferenceValidator.Path(path, "ownerId")));
        if (!Enum.IsDefined(resource.Status))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "Schema implementation status must be defined.",
                ArtifactReferenceValidator.Path(path, "status"));
        }

        if (resource.Consumers.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "A schema resource must name at least one explicit consumer.",
                ArtifactReferenceValidator.Path(path, "consumers"));
        }
        else
        {
            ArtifactEnvelopeValidator<object>.ValidateDistinctIdentifiers(
                resource.Consumers,
                ArtifactReferenceValidator.Path(path, "consumers"),
                ArtifactDiagnosticIds.InvalidSchemaModule,
                diagnostics);
        }

        ValidateProvenance(resource, path, diagnostics);
        ValidateCompatibility(resource, path, diagnostics);
    }

    private static void ValidateProvenance(
        ProgramKitSchemaResource resource,
        string path,
        ArtifactDiagnosticBuilder diagnostics)
    {
        var provenancePath = ArtifactReferenceValidator.Path(path, "provenance");
        if (resource.Provenance is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "Schema provenance is required.",
                provenancePath);
            return;
        }

        ArtifactEnvelopeValidator<object>.ValidateReferences(
            resource.Provenance.SourceInputs,
            ArtifactReferenceValidator.Path(provenancePath, "sourceInputs"),
            expectedKind: null,
            requireAtLeastOne: true,
            ArtifactDiagnosticIds.InvalidSchemaModule,
            diagnostics);
        diagnostics.Add(ProgramKitIdentifier.Validate(
            resource.Provenance.Producer.Value,
            ArtifactReferenceValidator.Path(provenancePath, "producer")));
        if (string.IsNullOrWhiteSpace(resource.Provenance.CorrelationId))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "Schema provenance correlation ID must be supplied.",
                ArtifactReferenceValidator.Path(provenancePath, "correlationId"));
        }

        ArtifactEnvelopeSelfReference.RejectAll(
            resource.SchemaReference,
            resource.Provenance.SourceInputs,
            ArtifactReferenceValidator.Path(provenancePath, "sourceInputs"),
            diagnostics);
    }

    private static void ValidateCompatibility(
        ProgramKitSchemaResource resource,
        string path,
        ArtifactDiagnosticBuilder diagnostics)
    {
        var compatibilityPath = ArtifactReferenceValidator.Path(path, "compatibility");
        if (resource.Compatibility is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "Schema compatibility metadata is required.",
                compatibilityPath);
            return;
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(
            resource.Compatibility.Policy.Value,
            ArtifactReferenceValidator.Path(compatibilityPath, "policy")));
        diagnostics.Add(SemanticVersionRange.Validate(
            resource.Compatibility.ReaderRange.Value,
            ArtifactReferenceValidator.Path(compatibilityPath, "readerRange")));
        diagnostics.Add(SemanticVersionRange.Validate(
            resource.Compatibility.WriterRange.Value,
            ArtifactReferenceValidator.Path(compatibilityPath, "writerRange")));
        if (resource.Compatibility.Dimensions.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidSchemaModule,
                "Schema compatibility must classify at least one dimension.",
                ArtifactReferenceValidator.Path(compatibilityPath, "dimensions"));
        }
        else
        {
            var dimensions = new HashSet<CompatibilityDimension>();
            for (var index = 0; index < resource.Compatibility.Dimensions.Length; index++)
            {
                var claim = resource.Compatibility.Dimensions[index];
                var claimPath = string.Concat(compatibilityPath, "/dimensions/", index);
                if (claim is null ||
                    !Enum.IsDefined(claim.Dimension) ||
                    !Enum.IsDefined(claim.Classification))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidSchemaModule,
                        "Schema compatibility claims must use defined values.",
                        claimPath);
                    continue;
                }

                if (!dimensions.Add(claim.Dimension))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidSchemaModule,
                        "Schema compatibility dimensions must be unique.",
                        ArtifactReferenceValidator.Path(claimPath, "dimension"));
                }

                if (claim.Classification ==
                        CompatibilityClassification.ConditionallyCompatible &&
                    claim.Conditions.IsDefaultOrEmpty)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidSchemaModule,
                        "Conditional schema compatibility requires explicit conditions.",
                        ArtifactReferenceValidator.Path(claimPath, "conditions"));
                }

                ArtifactEnvelopeValidator<object>.ValidateNonEmptyStrings(
                    claim.Conditions,
                    ArtifactReferenceValidator.Path(claimPath, "conditions"),
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    diagnostics);
            }
        }

        ArtifactEnvelopeValidator<object>.ValidateReferences(
            resource.Compatibility.MigrationReferences,
            ArtifactReferenceValidator.Path(compatibilityPath, "migrationReferences"),
            expectedKind: "migration",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidSchemaModule,
            diagnostics);
        ArtifactEnvelopeSelfReference.RejectAll(
            resource.SchemaReference,
            resource.Compatibility.MigrationReferences,
            ArtifactReferenceValidator.Path(compatibilityPath, "migrationReferences"),
            diagnostics);
    }
}
