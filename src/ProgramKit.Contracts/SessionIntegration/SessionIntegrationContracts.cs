using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.SessionIntegration;

public enum SessionLifecycleOperation { Explain, Install, Verify, Remove }
public enum SessionIntegrationState { Absent, Draft, Sealed, PublishedUnadmitted, Admitted, Exact, Stale, Drifted, Incompatible, Partial, Removed }
public enum SessionAvailability { NotEvaluated, ReloadRequired, Available, Unavailable }
public enum SessionProviderSupport { Supported, Incompatible, NotEvaluated }
public enum SessionBindingKind { ShellCli }
public enum DisclosureClassification { Public, RepositoryRelative, Withheld }

public sealed record DisclosureEntry(string Field, DisclosureClassification Classification, string Action);

public sealed record CliReleaseIdentity(
    string Schema,
    string CanonicalProfile,
    string PackageId,
    string PackageVersion,
    GovernedIdentity PackageSource,
    string PackageDigest,
    string CommandName,
    string WorkspaceRelativeExecutable,
    string ExecutableDigest,
    string ReportedVersion,
    GovernedIdentity RuntimeProfile,
    ClaimClass ClaimClass);

public sealed record SessionOperationBinding(string Name, GovernedIdentity Contract, EffectState Effect);

public sealed record CanonicalSessionIntegrationDefinition(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity Identity,
    IReadOnlyList<SessionOperationBinding> OperationContracts,
    IReadOnlyList<SessionOperationBinding> SessionLifecycleContracts,
    ArtifactReference GuidanceArtifact,
    string Fingerprint,
    string Revision);

public sealed record SessionProjectionDescriptor(
    string Role,
    string LogicalPath,
    string MediaType,
    ArtifactOwnership Ownership,
    ClaimClass ClaimClass,
    string RemovalPolicy);

public sealed record SessionProviderManifest(
    string Schema,
    GovernedIdentity ProviderIdentity,
    GovernedIdentity AdapterIdentity,
    GovernedIdentity DefinitionBinding,
    SessionBindingKind BindingKind,
    IReadOnlyList<string> SupportedScopes,
    IReadOnlyList<SessionProjectionDescriptor> ProjectionDescriptors,
    IReadOnlyList<string> RequiredCliOperations,
    GovernedIdentity DiagnosticCatalog,
    GovernedIdentity ConformanceProfile,
    SessionProviderSupport SupportClaim,
    string SurfaceRevision,
    string Revision);

public sealed record SessionProviderSelection(
    GovernedIdentity Provider,
    GovernedIdentity Adapter,
    GovernedIdentity Definition,
    GovernedIdentity ConformanceProfile);

public sealed record SessionWorkspaceBinding(GovernedIdentity Identity, string RootBindingDigest);

public sealed record RequestBoundAuthorityGrant(
    string Schema,
    string GrantIdentity,
    string WorkspaceIdentity,
    string Operation,
    string Effect,
    string RequestIdentity,
    string Provider,
    string Scope,
    DateTimeOffset NotBefore,
    DateTimeOffset NotAfter,
    bool Revoked,
    bool Consumed);

public sealed record AuthorityDemand(
    string WorkspaceIdentity,
    string Operation,
    RequestedEffect Effect,
    string RequestIdentity,
    string Provider,
    string Scope,
    DateTimeOffset EvaluationInstant);

public sealed record SessionIntegrationRequest(
    string Schema,
    string CanonicalProfile,
    SessionLifecycleOperation Operation,
    EvaluationContext EvaluationContext,
    SessionWorkspaceBinding Workspace,
    string Scope,
    SessionProviderSelection ProviderSelection,
    CliReleaseIdentity CliRelease,
    RequestedEffect RequestedEffect,
    string RequestCoreIdentity,
    string RequestIdentity,
    string? ExpectedInstallationState,
    RequestBoundAuthorityGrant? AuthorityGrant);

public sealed record SessionProjectionArtifact(
    string LogicalPath,
    string MediaType,
    ArtifactOwnership Ownership,
    GovernedIdentity ProducerIdentity,
    GovernedIdentity DefinitionBinding,
    string ContentDigest,
    ClaimClass ClaimClass,
    string RemovalPolicy);

public sealed record SessionPublicationEvidence(
    string JournalLogicalPath,
    string JournalDigest,
    string LiveStateDigest,
    string State);

public sealed record SessionInstallationRecord(
    string Schema,
    GovernedIdentity InstallationIdentity,
    string RequestIdentity,
    string RequestCoreIdentity,
    SessionWorkspaceBinding WorkspaceIdentity,
    string Scope,
    GovernedIdentity Definition,
    SessionProviderSelection Provider,
    CliReleaseIdentity CliRelease,
    IReadOnlyList<SessionProjectionArtifact> ProjectionSet,
    SessionPublicationEvidence Publication,
    SessionIntegrationState State,
    SessionAvailability SessionAvailability,
    string AdmissionReceipt,
    string RecordDigest);

public sealed record SessionProjectionObservation(string LogicalPath, string ExpectedDigest, string? ObservedDigest, string State);

public sealed record SessionVerification(
    SessionIntegrationState ObservedState,
    string? InstallationBinding,
    IReadOnlyList<SessionProjectionObservation> ProjectionObservations,
    SessionAvailability SessionAvailability,
    EffectState EffectState);
