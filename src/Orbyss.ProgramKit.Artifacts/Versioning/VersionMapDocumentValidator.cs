namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Validates immutable version-map graph snapshots.</summary>
public sealed class VersionMapDocumentValidator :
    IArtifactEnvelopeSemanticValidator<VersionMapDocument>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public VersionMapDocumentValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionMapDocument value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
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
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Add(envelopeValidator.Validate(envelope, this));
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
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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

            DefaultArtifactEnvelopeValidator.ValidateReferences(
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
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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
            DefaultArtifactEnvelopeValidator.ValidateReferences(
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
