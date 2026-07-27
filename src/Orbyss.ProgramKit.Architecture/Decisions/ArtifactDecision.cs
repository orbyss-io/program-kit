using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>One outcome's answered nine-question artifact decision.</summary>
public sealed record ArtifactDecision(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string RequestedOutcome,
    SupportedArtifactKind ArtifactKind,
    ExecutableBehaviorAnswer ExecutableBehavior,
    ValueLifecycleAnswer ValueLifecycle,
    AgentRetrievalAnswer AgentRetrieval,
    AgentProcedureAnswer AgentProcedure,
    HumanCommunicationAnswer HumanCommunication,
    GeneratedNavigationAnswer GeneratedNavigation,
    RepresentationAnswer Representation,
    GovernanceAnswer Governance,
    DataHandlingAnswer DataHandling,
    string Rationale);
