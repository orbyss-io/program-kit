using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Validates all nine mandatory artifact-decision answers.</summary>
public sealed class ArtifactDecisionValidator :
    IArtifactDecisionValidator
{
    private readonly ISupportedArtifactKindOwnershipResolver ownershipResolver;

    /// <summary>Initializes the validator with canonical ownership resolution.</summary>
    public ArtifactDecisionValidator(
        ISupportedArtifactKindOwnershipResolver ownershipResolver)
    {
        this.ownershipResolver = ownershipResolver ??
            throw new ArgumentNullException(nameof(ownershipResolver));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactDecision value) =>
        Validate(value, "/");

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactDecision value, string path)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc300,
                path,
                "An artifact decision is required.");
            return diagnostics.ToResult();
        }

        ValidateInto(value, path, diagnostics);
        return diagnostics.ToResult();
    }

    private void ValidateInto(
        ArtifactDecision decision,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        diagnostics.Identifier(decision.Identity, $"{path}identity");
        diagnostics.Identifier(decision.OwnerId, $"{path}ownerId");
        diagnostics.Required(
            decision.RequestedOutcome,
            $"{path}requestedOutcome",
            "Requested outcome");
        diagnostics.Required(decision.Rationale, $"{path}rationale", "Artifact decision rationale");
        ValidateOwnership(decision, path, diagnostics);

        ValidateExecutableBehavior(decision.ExecutableBehavior, $"{path}executableBehavior", diagnostics);
        ValidateValueLifecycle(decision.ValueLifecycle, $"{path}valueLifecycle", diagnostics);
        ValidateAgentRetrieval(decision.AgentRetrieval, $"{path}agentRetrieval", diagnostics);
        ValidateAgentProcedure(decision.AgentProcedure, $"{path}agentProcedure", diagnostics);
        ValidateHumanCommunication(
            decision.HumanCommunication,
            $"{path}humanCommunication",
            diagnostics);
        ValidateGeneratedNavigation(
            decision.GeneratedNavigation,
            $"{path}generatedNavigation",
            diagnostics);
        ValidateRepresentation(decision.Representation, $"{path}representation", diagnostics);
        ValidateGovernance(decision, $"{path}governance", diagnostics);
        ValidateDataHandling(decision.DataHandling, $"{path}dataHandling", diagnostics);
        ValidateKindConsistency(decision, path, diagnostics);
    }

    private void ValidateOwnership(
        ArtifactDecision decision,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!Enum.IsDefined(decision.ArtifactKind))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc328,
                $"{path}artifactKind",
                "The artifact kind has no canonical ownership rule.");
            return;
        }

        var ownership = ownershipResolver.Resolve(decision.ArtifactKind);
        if (!ownership.ArtifactIdentityKinds.Contains(
                decision.Identity.Kind,
                StringComparer.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc329,
                $"{path}identity",
                $"Artifact kind '{decision.ArtifactKind}' requires identity kind " +
                $"[{string.Join(", ", ownership.ArtifactIdentityKinds)}], not '{decision.Identity.Kind}'.");
        }

        if (!ownership.OwnerIdentityKinds.Contains(
                decision.OwnerId.Kind,
                StringComparer.Ordinal))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc330,
                $"{path}ownerId",
                $"Artifact kind '{decision.ArtifactKind}' requires owner kind " +
                $"[{string.Join(", ", ownership.OwnerIdentityKinds)}], not '{decision.OwnerId.Kind}'.");
        }
    }

    private static void ValidateExecutableBehavior(
        ExecutableBehaviorAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc301, path, "Question 1 must be answered.");
            return;
        }

        diagnostics.Required(answer.Rationale, $"{path}/rationale", "Executable-behavior rationale");
    }

    private static void ValidateValueLifecycle(
        ValueLifecycleAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc302, path, "Question 2 must be answered.");
            return;
        }

        var uses = ArchitectureValidation.OrEmpty(answer.Uses);
        for (var index = 0; index < uses.Length; index++)
        {
            if (!Enum.IsDefined(uses[index]))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc331,
                    $"{path}/uses/{index}",
                    "The value-lifecycle use is unsupported.");
            }
        }

        if (uses.Distinct().Count() != uses.Length)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc303,
                $"{path}/uses",
                "Value lifecycle uses must not contain duplicates.");
        }

        diagnostics.Required(answer.Rationale, $"{path}/rationale", "Value-lifecycle rationale");
    }

    private static void ValidateAgentRetrieval(
        AgentRetrievalAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc304, path, "Question 3 must be answered.");
            return;
        }

        if (answer.IsRequired)
        {
            diagnostics.Required(
                answer.RetrievalBoundary,
                $"{path}/retrievalBoundary",
                "Agent retrieval boundary");
        }
        else if (!string.IsNullOrEmpty(answer.RetrievalBoundary))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc305,
                $"{path}/retrievalBoundary",
                "A retrieval boundary cannot be supplied when agent retrieval is not required.");
        }

        diagnostics.Required(answer.Rationale, $"{path}/rationale", "Agent-retrieval rationale");
    }

    private static void ValidateAgentProcedure(
        AgentProcedureAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc306, path, "Question 4 must be answered.");
            return;
        }

        if (answer.IsRequired)
        {
            diagnostics.Required(
                answer.HumanStartBoundary,
                $"{path}/humanStartBoundary",
                "Human-start boundary");
            diagnostics.Required(
                answer.ProcedureBoundary,
                $"{path}/procedureBoundary",
                "Agent procedure boundary");
        }
        else if (!string.IsNullOrEmpty(answer.HumanStartBoundary) ||
                 !string.IsNullOrEmpty(answer.ProcedureBoundary))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc307,
                path,
                "Procedure boundaries cannot be supplied when an agent procedure is not required.");
        }

        diagnostics.Required(answer.Rationale, $"{path}/rationale", "Agent-procedure rationale");
    }

    private static void ValidateHumanCommunication(
        HumanCommunicationAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc308, path, "Question 5 must be answered.");
            return;
        }

        if (answer.IsRequired)
        {
            diagnostics.Required(answer.Audience, $"{path}/audience", "Human audience");
            diagnostics.Required(
                answer.DecisionAuthorityBoundary,
                $"{path}/decisionAuthorityBoundary",
                "Human decision-authority boundary");
        }
        else if (!string.IsNullOrEmpty(answer.Audience) ||
                 !string.IsNullOrEmpty(answer.DecisionAuthorityBoundary))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc309,
                path,
                "Human communication fields cannot be supplied when human communication is not required.");
        }

        diagnostics.Required(
            answer.Rationale,
            $"{path}/rationale",
            "Human-communication rationale");
    }

    private static void ValidateGeneratedNavigation(
        GeneratedNavigationAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc310, path, "Question 6 must be answered.");
            return;
        }

        var sources = ArchitectureValidation.OrEmpty(answer.SourceIds);
        if (answer.IsRequired)
        {
            if (sources.Length == 0)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc311,
                    $"{path}/sourceIds",
                    "Generated navigation requires at least one source identity.");
            }

            diagnostics.Required(
                answer.GenerationRule,
                $"{path}/generationRule",
                "Navigation generation rule");
        }
        else if (sources.Length > 0 || !string.IsNullOrEmpty(answer.GenerationRule))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc312,
                path,
                "Navigation sources and rules cannot be supplied when generation is not required.");
        }

        for (var index = 0; index < sources.Length; index++)
        {
            diagnostics.Identifier(sources[index], $"{path}/sourceIds/{index}");
        }

        diagnostics.Required(
            answer.Rationale,
            $"{path}/rationale",
            "Generated-navigation rationale");
    }

    private static void ValidateRepresentation(
        RepresentationAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc313, path, "Question 7 must be answered.");
            return;
        }

        switch (answer.Role)
        {
            case ArtifactRepresentationRole.Canonical:
                if (answer.CanonicalArtifactId is not null ||
                    !string.IsNullOrEmpty(answer.ProjectionRule) ||
                    !string.IsNullOrEmpty(answer.LossPolicy))
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc314,
                        path,
                        "A canonical artifact cannot point to another canonical artifact or declare projection semantics.");
                }

                break;
            case ArtifactRepresentationRole.Projection:
                if (answer.CanonicalArtifactId is null)
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc315,
                        $"{path}/canonicalArtifactId",
                        "A projection must name its canonical artifact.");
                }
                else
                {
                    diagnostics.Identifier(answer.CanonicalArtifactId.Value, $"{path}/canonicalArtifactId");
                }

                diagnostics.Required(answer.ProjectionRule, $"{path}/projectionRule", "Projection rule");
                diagnostics.Required(answer.LossPolicy, $"{path}/lossPolicy", "Projection loss policy");
                break;
            case ArtifactRepresentationRole.Ephemeral:
                if (answer.CanonicalArtifactId is not null ||
                    !string.IsNullOrEmpty(answer.ProjectionRule))
                {
                    diagnostics.Error(
                        ArchitectureDiagnosticIds.Pkarc316,
                        path,
                        "Ephemeral state cannot claim a canonical source representation or projection rule.");
                }

                diagnostics.Required(answer.LossPolicy, $"{path}/lossPolicy", "Ephemeral loss policy");
                break;
            default:
                diagnostics.Error(ArchitectureDiagnosticIds.Pkarc317, $"{path}/role", "Representation role is unsupported.");
                break;
        }
    }

    private static void ValidateGovernance(
        ArtifactDecision decision,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var answer = decision.Governance;
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc318, path, "Question 8 must be answered.");
            return;
        }

        diagnostics.Identifier(answer.ArtifactIdentity, $"{path}/artifactIdentity");
        diagnostics.Identifier(answer.OwnerId, $"{path}/ownerId");
        if (answer.ArtifactIdentity != decision.Identity)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc319,
                $"{path}/artifactIdentity",
                "Governance identity must equal the artifact decision identity.");
        }

        if (answer.OwnerId != decision.OwnerId)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc320,
                $"{path}/ownerId",
                "Governance owner must equal the artifact decision owner.");
        }

        if (answer.Schema is not null)
        {
            diagnostics.Reference(answer.Schema, $"{path}/schema");
        }

        diagnostics.Required(answer.ProvenancePolicy, $"{path}/provenancePolicy", "Provenance policy");
        diagnostics.Required(answer.DigestPolicy, $"{path}/digestPolicy", "Digest policy");
        diagnostics.Required(
            answer.CompatibilityPolicy,
            $"{path}/compatibilityPolicy",
            "Compatibility policy");
        diagnostics.Required(answer.MigrationPolicy, $"{path}/migrationPolicy", "Migration policy");

        var consumers = ArchitectureValidation.OrEmpty(answer.ConsumerIds);
        for (var index = 0; index < consumers.Length; index++)
        {
            diagnostics.Identifier(consumers[index], $"{path}/consumerIds/{index}");
        }
    }

    private static void ValidateDataHandling(
        DataHandlingAnswer? answer,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (answer is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc321, path, "Question 9 must be answered.");
            return;
        }

        diagnostics.Required(answer.RedactionPolicy, $"{path}/redactionPolicy", "Redaction policy");
        diagnostics.Required(
            answer.ExternalizationPolicy,
            $"{path}/externalizationPolicy",
            "Externalization policy");
        diagnostics.Required(
            answer.EphemeralDataPolicy,
            $"{path}/ephemeralDataPolicy",
            "Ephemeral-data policy");
    }

    private static void ValidateKindConsistency(
        ArtifactDecision decision,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (decision.Representation is null || decision.DataHandling is null)
        {
            return;
        }

        if (decision.ArtifactKind == SupportedArtifactKind.ContractDefinedEphemeralState &&
            decision.Representation.Role != ArtifactRepresentationRole.Ephemeral)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc322,
                $"{path}representation/role",
                "Contract-defined ephemeral state must select the ephemeral representation role.");
        }

        if (decision.ArtifactKind != SupportedArtifactKind.ContractDefinedEphemeralState &&
            decision.Representation.Role == ArtifactRepresentationRole.Ephemeral)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc323,
                $"{path}artifactKind",
                "Only contract-defined ephemeral state may select the ephemeral representation role.");
        }

        if (decision.Representation.Role == ArtifactRepresentationRole.Canonical &&
            decision.DataHandling.ContainsEphemeralData)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc324,
                $"{path}dataHandling/containsEphemeralData",
                "Ephemeral data is forbidden in a canonical source artifact.");
        }

        if (decision.ArtifactKind is
            SupportedArtifactKind.ProviderNeutralAgentInstruction or
            SupportedArtifactKind.ProviderNeutralAgentCapability)
        {
            if (decision.AgentRetrieval?.IsRequired != true ||
                decision.AgentProcedure?.IsRequired != true)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc325,
                    $"{path}artifactKind",
                    "An agent instruction or capability requires bounded retrieval and procedure answers.");
            }
        }

        if (decision.ArtifactKind is
            SupportedArtifactKind.HumanDocument or
            SupportedArtifactKind.HumanDecisionRecord &&
            decision.HumanCommunication?.IsRequired != true)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc326,
                $"{path}artifactKind",
                "A human document or decision record requires a human-communication answer.");
        }

        if (decision.ArtifactKind is
            SupportedArtifactKind.GeneratedCatalog or
            SupportedArtifactKind.GeneratedIndex &&
            decision.GeneratedNavigation?.IsRequired != true)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc327,
                $"{path}artifactKind",
                "A generated catalog or index requires generated navigation.");
        }
    }
}
