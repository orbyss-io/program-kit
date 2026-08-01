using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

public enum ClaudeAuthenticationState { NotEvaluated, Available, Unavailable }
public enum ClaudeWorkspaceTrustState { NotEvaluated, Required, Accepted, Rejected }
public enum ClaudeSkillDiscoveryState { NotEvaluated, ReloadRequired, Available, Unavailable }
public enum ClaudeTrialMode { ExplicitSkill, NaturalDiscovery, InteractiveReview }
public enum ClaudeBehaviorVerdict { Preserved, Violated, NotEvaluated }
public enum ClaudeTrialStatus { Passed, Failed, Incompatible, Inconclusive, NotEvaluated }
public enum ClaudeEvidenceVerdictValue { Passed, Failed, NotEvaluated }
public enum ClaudeHumanDecision { Accepted, Rejected, Pending }

public sealed record ClaudeProviderObservation(
    string ObservationIdentity,
    DateTimeOffset EvaluationInstant,
    GovernedIdentity EnvironmentIdentity,
    GovernedIdentity ProviderIdentity,
    string ReportedVersion,
    string ExecutableDigest,
    ClaudeAuthenticationState AuthenticationState,
    ClaudeWorkspaceTrustState WorkspaceTrustState,
    ClaudeSkillDiscoveryState SkillDiscoveryState,
    IReadOnlyList<string> Limitations);

public sealed record ClaudeConformanceCase(
    GovernedIdentity CaseIdentity,
    string CanonicalOperation,
    string RequestIdentity,
    string ExpectedScope,
    EffectState ExpectedEffect,
    PrimaryDisposition ExpectedDisposition,
    IReadOnlyList<string> ExpectedDiagnostics,
    string ObservedResultIdentity,
    ClaudeTrialStatus Status);

public sealed record ClaudeLiveTrial(
    string TrialIdentity,
    int Ordinal,
    ClaudeTrialMode Mode,
    string ProviderObservation,
    GovernedIdentity CaseIdentity,
    IReadOnlyList<ArtifactReference> ProgramKitEvidence,
    string EffectObservation,
    ClaudeBehaviorVerdict AuthorityBehavior,
    ClaudeBehaviorVerdict DiagnosticBehavior,
    ClaudeTrialStatus Status);

public sealed record ClaudeConformanceSummary(
    GovernedIdentity Profile,
    GovernedIdentity Corpus,
    int Passed,
    int Failed,
    int Incompatible,
    int Inconclusive,
    int NotEvaluated);

public sealed record ClaudeEvidenceVerdict(
    ClaudeEvidenceVerdictValue Verdict,
    ArtifactReference Evidence);

public sealed record ClaudeMachineReviewRecord(
    string Schema,
    string CanonicalProfile,
    string ReviewIdentity,
    DateTimeOffset EvaluationInstant,
    GovernedIdentity Environment,
    GovernedIdentity CliRelease,
    GovernedIdentity Definition,
    GovernedIdentity Adapter,
    GovernedIdentity Provider,
    ArtifactReference Installation,
    ClaudeConformanceSummary ConformanceSummary,
    IReadOnlyList<ClaudeLiveTrial> LiveTrials,
    ClaudeEvidenceVerdict RuntimeIsolation,
    ClaudeEvidenceVerdict DisclosureReview,
    ClaudeHumanDecision HumanDecision,
    IReadOnlyList<string> Limitations);
