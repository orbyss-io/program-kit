namespace Orbyss.ProgramKit.Artifacts;

/// <summary>Validates versioned component manifests.</summary>
public sealed class VersionedComponentManifestValidator :
    IProgramKitSemanticValidator<VersionedComponentManifest>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionedComponentManifest value)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "A versioned component manifest is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, "/identity"));
        diagnostics.Add(ProgramKitIdentifier.Validate(value.OwnerId.Value, "/ownerId"));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, "/version"));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, "/digest"));
        if (!Enum.IsDefined(value.Kind))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "The component boundary kind is not defined.",
                "/kind");
        }

        ArtifactEnvelopeValidator<object>.ValidateReferences(
            value.ProvidedContracts,
            "/providedContracts",
            expectedKind: "contract",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidComponentManifest,
            diagnostics);
        ValidateRequirements(value, diagnostics);
        ValidateCompatibilityClaims(value, diagnostics);
        ArtifactEnvelopeValidator<object>.ValidateReferences(
            value.MigrationReferences,
            "/migrationReferences",
            expectedKind: "migration",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidComponentManifest,
            diagnostics);
        return diagnostics.ToResult();
    }

    private static void ValidateRequirements(
        VersionedComponentManifest manifest,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (manifest.RequiredContracts.IsDefault)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "The required-contract collection must be initialized.",
                "/requiredContracts");
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < manifest.RequiredContracts.Length; index++)
        {
            var requirement = manifest.RequiredContracts[index];
            var path = string.Concat("/requiredContracts/", index);
            if (requirement is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A version requirement is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                requirement.Identity.Value,
                ArtifactReferenceValidator.Path(path, "identity")));
            diagnostics.Add(SemanticVersionRange.Validate(
                requirement.AcceptedRange.Value,
                ArtifactReferenceValidator.Path(path, "acceptedRange")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                requirement.Resolution,
                ArtifactReferenceValidator.Path(path, "resolution")));
            if (!Enum.IsDefined(requirement.Exposure))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "Dependency exposure is not defined.",
                    ArtifactReferenceValidator.Path(path, "exposure"));
            }

            if (requirement.Resolution is not null)
            {
                if (requirement.Identity != requirement.Resolution.Identity)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidComponentManifest,
                        "The resolution identity must equal the required identity.",
                        ArtifactReferenceValidator.Path(path, "resolution/identity"));
                }

                if (!requirement.AcceptedRange.Contains(requirement.Resolution.Version))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidComponentManifest,
                        "The exact resolution is outside the accepted range.",
                        ArtifactReferenceValidator.Path(path, "resolution/version"));
                }
            }

            ValidateDimensions(
                requirement.Dimensions,
                ArtifactReferenceValidator.Path(path, "dimensions"),
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
            ArtifactEnvelopeValidator<object>.ValidateReferences(
                requirement.EvidenceReferences,
                ArtifactReferenceValidator.Path(path, "evidenceReferences"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
            if (!seen.Add(requirement.Identity.Value))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A manifest may require a contract identity only once.",
                    ArtifactReferenceValidator.Path(path, "identity"));
            }
        }
    }

    private static void ValidateCompatibilityClaims(
        VersionedComponentManifest manifest,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (manifest.CompatibilityClaims.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "At least one compatibility claim is required.",
                "/compatibilityClaims");
            return;
        }

        var seen = new HashSet<CompatibilityDimension>();
        for (var index = 0; index < manifest.CompatibilityClaims.Length; index++)
        {
            var claim = manifest.CompatibilityClaims[index];
            var path = string.Concat("/compatibilityClaims/", index);
            if (claim is null ||
                !Enum.IsDefined(claim.Dimension) ||
                !Enum.IsDefined(claim.Classification))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A compatibility claim must use defined values.",
                    path);
                continue;
            }

            if (!seen.Add(claim.Dimension))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A compatibility dimension may be claimed only once.",
                    ArtifactReferenceValidator.Path(path, "dimension"));
            }

            if (claim.Classification == CompatibilityClassification.ConditionallyCompatible &&
                claim.Conditions.IsDefaultOrEmpty)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "Conditional compatibility requires explicit conditions.",
                    ArtifactReferenceValidator.Path(path, "conditions"));
            }

            ArtifactEnvelopeValidator<object>.ValidateNonEmptyStrings(
                claim.Conditions,
                ArtifactReferenceValidator.Path(path, "conditions"),
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
        }
    }

    internal static void ValidateDimensions(
        System.Collections.Immutable.ImmutableArray<CompatibilityDimension> dimensions,
        string path,
        string diagnosticId,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (dimensions.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                diagnosticId,
                "At least one compatibility dimension is required.",
                path);
            return;
        }

        var seen = new HashSet<CompatibilityDimension>();
        for (var index = 0; index < dimensions.Length; index++)
        {
            if (!Enum.IsDefined(dimensions[index]) || !seen.Add(dimensions[index]))
            {
                diagnostics.Error(
                    diagnosticId,
                    "Compatibility dimensions must be defined and unique.",
                    string.Concat(path, "/", index));
            }
        }
    }
}

/// <summary>Validates immutable version-map graph snapshots.</summary>
public sealed class VersionMapDocumentValidator :
    IProgramKitSemanticValidator<VersionMapDocument>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionMapDocument value)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionMap,
                "A version map is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        var exactNodes = ValidateNodes(value, diagnostics);
        ValidateEdges(value, exactNodes, diagnostics);
        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates the envelope and rejects exact references from the version-map
    /// payload back to that same envelope revision.
    /// </summary>
    /// <remarks>
    /// This overload detects cycles from the supplied envelope reference only.
    /// Canonical-byte digest recomputation and verification remain W015 work.
    /// </remarks>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<VersionMapDocument> envelope)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        diagnostics.Add(
            new ArtifactEnvelopeValidator<VersionMapDocument>(this).Validate(envelope));
        if (envelope?.Document is null ||
            !ArtifactEnvelopeSelfReference.TryCreate(envelope, out var selfReference))
        {
            return diagnostics.ToResult();
        }

        for (var nodeIndex = 0; nodeIndex < envelope.Document.Nodes.Length; nodeIndex++)
        {
            var node = envelope.Document.Nodes[nodeIndex];
            if (node is null)
            {
                continue;
            }

            var nodePath = string.Concat("/document/nodes/", nodeIndex);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                node.Revision,
                ArtifactReferenceValidator.Path(nodePath, "revision"),
                diagnostics);
            ArtifactEnvelopeSelfReference.RejectAll(
                selfReference,
                node.EvidenceReferences,
                ArtifactReferenceValidator.Path(nodePath, "evidenceReferences"),
                diagnostics);
        }

        for (var edgeIndex = 0; edgeIndex < envelope.Document.Edges.Length; edgeIndex++)
        {
            var edge = envelope.Document.Edges[edgeIndex];
            if (edge is null)
            {
                continue;
            }

            var edgePath = string.Concat("/document/edges/", edgeIndex);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                edge.Source,
                ArtifactReferenceValidator.Path(edgePath, "source"),
                diagnostics);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                edge.Resolution,
                ArtifactReferenceValidator.Path(edgePath, "resolution"),
                diagnostics);
            ArtifactEnvelopeSelfReference.RejectAll(
                selfReference,
                edge.EvidenceReferences,
                ArtifactReferenceValidator.Path(edgePath, "evidenceReferences"),
                diagnostics);
        }

        return diagnostics.ToResult();
    }

    private static HashSet<string> ValidateNodes(
        VersionMapDocument map,
        ArtifactDiagnosticBuilder diagnostics)
    {
        var exactNodes = new HashSet<string>(StringComparer.Ordinal);
        if (map.Nodes.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionMap,
                "A version map must contain at least one revision node.",
                "/nodes");
            return exactNodes;
        }

        var revisionDigests = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var index = 0; index < map.Nodes.Length; index++)
        {
            var node = map.Nodes[index];
            var path = string.Concat("/nodes/", index);
            if (node is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "A version-map node is required.",
                    path);
                continue;
            }

            diagnostics.Add(ArtifactReferenceValidator.Validate(
                node.Revision,
                ArtifactReferenceValidator.Path(path, "revision")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                node.OwnerId.Value,
                ArtifactReferenceValidator.Path(path, "ownerId")));
            if (!Enum.IsDefined(node.Kind))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "The version boundary kind is not defined.",
                    ArtifactReferenceValidator.Path(path, "kind"));
            }

            ArtifactEnvelopeValidator<object>.ValidateReferences(
                node.EvidenceReferences,
                ArtifactReferenceValidator.Path(path, "evidenceReferences"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidVersionMap,
                diagnostics);
            if (node.Revision is null)
            {
                continue;
            }

            var revisionKey = ArtifactReferenceValidator.Key(node.Revision);
            if (revisionDigests.TryGetValue(revisionKey, out var digest) &&
                !string.Equals(digest, node.Revision.Digest.Value, StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.RevisionDigestConflict,
                    "Equal identity and version nodes must resolve to equal digests.",
                    ArtifactReferenceValidator.Path(path, "revision/digest"));
            }
            else
            {
                revisionDigests[revisionKey] = node.Revision.Digest.Value;
            }

            if (!exactNodes.Add(ArtifactReferenceValidator.ExactKey(node.Revision)))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "Duplicate exact revision nodes are not allowed.",
                    ArtifactReferenceValidator.Path(path, "revision"));
            }
        }

        return exactNodes;
    }

    private static void ValidateEdges(
        VersionMapDocument map,
        HashSet<string> exactNodes,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (map.Edges.IsDefault)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionMap,
                "The version-map edge collection must be initialized.",
                "/edges");
            return;
        }

        var edgeIds = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < map.Edges.Length; index++)
        {
            var edge = map.Edges[index];
            var path = string.Concat("/edges/", index);
            if (edge is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "A version-map edge is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                edge.Id.Value,
                ArtifactReferenceValidator.Path(path, "id")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                edge.Source,
                ArtifactReferenceValidator.Path(path, "source")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                edge.TargetIdentity.Value,
                ArtifactReferenceValidator.Path(path, "targetIdentity")));
            diagnostics.Add(SemanticVersionRange.Validate(
                edge.AcceptedRange.Value,
                ArtifactReferenceValidator.Path(path, "acceptedRange")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                edge.Resolution,
                ArtifactReferenceValidator.Path(path, "resolution")));

            if (!Enum.IsDefined(edge.Kind) || !Enum.IsDefined(edge.Exposure))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "The dependency kind and exposure must be defined.",
                    path);
            }

            VersionedComponentManifestValidator.ValidateDimensions(
                edge.CompatibilityDimensions,
                ArtifactReferenceValidator.Path(path, "compatibilityDimensions"),
                ArtifactDiagnosticIds.InvalidVersionMap,
                diagnostics);
            ArtifactEnvelopeValidator<object>.ValidateReferences(
                edge.EvidenceReferences,
                ArtifactReferenceValidator.Path(path, "evidenceReferences"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidVersionMap,
                diagnostics);

            if (!edgeIds.Add(edge.Id.Value))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "Version-map edge identities must be unique.",
                    ArtifactReferenceValidator.Path(path, "id"));
            }

            if (edge.Source is not null &&
                !exactNodes.Contains(ArtifactReferenceValidator.ExactKey(edge.Source)))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionMap,
                    "The edge source must be an exact node in this map.",
                    ArtifactReferenceValidator.Path(path, "source"));
            }

            if (edge.Resolution is not null)
            {
                if (!exactNodes.Contains(ArtifactReferenceValidator.ExactKey(edge.Resolution)))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidVersionMap,
                        "The edge resolution must be an exact node in this map.",
                        ArtifactReferenceValidator.Path(path, "resolution"));
                }

                if (edge.TargetIdentity != edge.Resolution.Identity)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidVersionMap,
                        "The exact resolution identity must equal targetIdentity.",
                        ArtifactReferenceValidator.Path(path, "resolution/identity"));
                }

                if (!edge.AcceptedRange.Contains(edge.Resolution.Version))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidVersionMap,
                        "The exact resolution is outside the accepted range.",
                        ArtifactReferenceValidator.Path(path, "resolution/version"));
                }
            }
        }
    }
}

/// <summary>Validates immutable observed-to-target selections.</summary>
public sealed class VersionSelectionDocumentValidator :
    IProgramKitSemanticValidator<VersionSelectionDocument>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionSelectionDocument value)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "A version selection document is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ArtifactReferenceValidator.Validate(value.InputVersionMap, "/inputVersionMap"));
        if (value.InputVersionMap is not null &&
            !string.Equals(value.InputVersionMap.Identity.Kind, "version-map", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "The input map reference must have PKID kind 'version-map'.",
                "/inputVersionMap/identity");
        }

        if (value.Selections.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "At least one exact selection is required.",
                "/selections");
            return diagnostics.ToResult();
        }

        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Selections.Length; index++)
        {
            var selection = value.Selections[index];
            var path = string.Concat("/selections/", index);
            if (selection is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "A version selection is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                selection.Identity.Value,
                ArtifactReferenceValidator.Path(path, "identity")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                selection.Observed,
                ArtifactReferenceValidator.Path(path, "observed")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                selection.Target,
                ArtifactReferenceValidator.Path(path, "target")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                selection.OwnerId.Value,
                ArtifactReferenceValidator.Path(path, "ownerId")));

            if (selection.Observed is not null && selection.Observed.Identity != selection.Identity)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "The observed reference identity must equal the selected identity.",
                    ArtifactReferenceValidator.Path(path, "observed/identity"));
            }

            if (selection.Target is not null && selection.Target.Identity != selection.Identity)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "The target reference identity must equal the selected identity.",
                    ArtifactReferenceValidator.Path(path, "target/identity"));
            }

            if (!identities.Add(selection.Identity.Value))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "A semantic identity may be selected only once.",
                    ArtifactReferenceValidator.Path(path, "identity"));
            }
        }

        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates the envelope and rejects exact references from the selection
    /// payload back to that same envelope revision.
    /// </summary>
    /// <remarks>
    /// This overload detects cycles from supplied metadata and does not
    /// recompute canonical bytes or the digest; that remains W015 work.
    /// </remarks>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<VersionSelectionDocument> envelope)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        diagnostics.Add(
            new ArtifactEnvelopeValidator<VersionSelectionDocument>(this).Validate(envelope));
        if (envelope?.Document is null ||
            !ArtifactEnvelopeSelfReference.TryCreate(envelope, out var selfReference))
        {
            return diagnostics.ToResult();
        }

        ArtifactEnvelopeSelfReference.Reject(
            selfReference,
            envelope.Document.InputVersionMap,
            "/document/inputVersionMap",
            diagnostics);
        for (var index = 0; index < envelope.Document.Selections.Length; index++)
        {
            var selection = envelope.Document.Selections[index];
            if (selection is null)
            {
                continue;
            }

            var path = string.Concat("/document/selections/", index);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                selection.Observed,
                ArtifactReferenceValidator.Path(path, "observed"),
                diagnostics);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                selection.Target,
                ArtifactReferenceValidator.Path(path, "target"),
                diagnostics);
        }

        return diagnostics.ToResult();
    }
}
