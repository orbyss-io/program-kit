using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Schemas;

/// <summary>Validates schema-module descriptors without opening resources or performing I/O.</summary>
public sealed class ProgramKitSchemaModuleValidator :
    IProgramKitSemanticValidator<IProgramKitSchemaModule>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(IProgramKitSchemaModule value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
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
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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
            DefaultArtifactEnvelopeValidator.ValidateDistinctIdentifiers(
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
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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

        DefaultArtifactEnvelopeValidator.ValidateReferences(
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
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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

                DefaultArtifactEnvelopeValidator.ValidateNonEmptyStrings(
                    claim.Conditions,
                    ArtifactReferenceValidator.Path(claimPath, "conditions"),
                    ArtifactDiagnosticIds.InvalidSchemaModule,
                    diagnostics);
            }
        }

        DefaultArtifactEnvelopeValidator.ValidateReferences(
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
