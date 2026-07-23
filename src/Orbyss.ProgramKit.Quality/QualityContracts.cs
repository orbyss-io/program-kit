using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Quality;

/// <summary>Identifies the durable purpose of a test specification.</summary>
public enum TestCategory
{
    /// <summary>Tests one isolated source unit.</summary>
    Unit,
    /// <summary>Tests one assembled component boundary.</summary>
    Component,
    /// <summary>Tests a published contract or conformance rule.</summary>
    ContractConformance,
    /// <summary>Tests registration and composition behavior.</summary>
    RegistrationComposition,
    /// <summary>Tests collaborating implementation boundaries.</summary>
    Integration,
    /// <summary>Tests an externally observable flow from end to end.</summary>
    EndToEnd,
    /// <summary>Preserves behavior implicated by a prior defect.</summary>
    Regression,
    /// <summary>Tests mechanical architecture constraints.</summary>
    Architecture,
    /// <summary>Tests an explicit security property.</summary>
    Security,
    /// <summary>Tests a bounded performance expectation.</summary>
    Performance,
    /// <summary>Tests repeatability from exact inputs.</summary>
    Reproducibility,
    /// <summary>Tests an explicit compatibility expectation.</summary>
    Compatibility,
    /// <summary>Records a selected human validation activity.</summary>
    HumanValidation,
}

/// <summary>Identifies the behavioral shape exercised by a scenario.</summary>
public enum TestScenarioKind
{
    /// <summary>Exercises accepted behavior.</summary>
    Positive,
    /// <summary>Exercises rejected input or behavior.</summary>
    Negative,
    /// <summary>Exercises a defined failure path.</summary>
    Failure,
    /// <summary>Exercises recovery after failure.</summary>
    Recovery,
    /// <summary>Exercises cancellation semantics.</summary>
    Cancellation,
    /// <summary>Exercises concurrent behavior.</summary>
    Concurrency,
    /// <summary>Exercises explicit migration behavior.</summary>
    Migration,
}

/// <summary>Constrains network access during an execution.</summary>
public enum NetworkAccessPolicy
{
    /// <summary>Forbids network access.</summary>
    Denied,
    /// <summary>Permits only loopback access.</summary>
    LoopbackOnly,
    /// <summary>Permits only explicitly listed destinations.</summary>
    ExplicitAllowList,
}

/// <summary>Constrains filesystem writes during an execution.</summary>
public enum WriteAccessPolicy
{
    /// <summary>Forbids filesystem writes.</summary>
    Denied,
    /// <summary>Permits writes only to the selected temporary output.</summary>
    TemporaryOutputOnly,
    /// <summary>Permits writes only beneath explicit roots.</summary>
    ExplicitRoots,
}

/// <summary>Constrains package or tool restore during an execution.</summary>
public enum RestoreAccessPolicy
{
    /// <summary>Forbids dependency restore.</summary>
    Denied,
    /// <summary>Permits restore only from an exact lock.</summary>
    LockedOnly,
}

/// <summary>Constrains secret access during an execution.</summary>
public enum SecretAccessPolicy
{
    /// <summary>Forbids secret access.</summary>
    Denied,
    /// <summary>Permits only explicitly named external secret references.</summary>
    ExplicitReferencesOnly,
}

/// <summary>Records the complete side-effect policy required by a specification or selected by a profile.</summary>
public sealed record TestExecutionAccessPolicy(
    NetworkAccessPolicy Network,
    ImmutableArray<string> AllowedNetworkDestinations,
    WriteAccessPolicy Writes,
    ImmutableArray<string> AllowedWriteRoots,
    RestoreAccessPolicy Restore,
    SecretAccessPolicy Secrets,
    ImmutableArray<string> AllowedSecretReferences);

/// <summary>Defines bounded retry behavior for a test execution.</summary>
public sealed record TestRetryPolicy(
    int MaximumAttempts,
    TimeSpan Delay);

/// <summary>Defines execution constraints without selecting a concrete runner environment.</summary>
public sealed record TestExecutionRequirements(
    ImmutableArray<string> RunnerClasses,
    ImmutableArray<string> Platforms,
    ImmutableArray<string> EnvironmentAssumptions,
    ImmutableArray<ArtifactReference> RequiredDependencyClosure,
    TestExecutionAccessPolicy Access,
    TimeSpan Timeout,
    TestRetryPolicy Retry);

/// <summary>Defines one durable scenario and its exact machine-contract inputs and fixtures.</summary>
public sealed record TestScenario(
    string ScenarioId,
    TestScenarioKind Kind,
    string Purpose,
    ImmutableArray<ArtifactReference> Inputs,
    ImmutableArray<ArtifactReference> Fixtures,
    string ExpectedResult);

/// <summary>Defines the expected overall result of a test specification.</summary>
public sealed record TestExpectedResult(
    string OutcomeCode,
    string Description);

/// <summary>Defines the observation names and optional attachment contract required in evidence.</summary>
public sealed record TestEvidenceShape(
    ArtifactReference Schema,
    ImmutableArray<string> RequiredObservations,
    bool AllowsAttachments);

/// <summary>
/// Describes durable test meaning independently from the environment used to execute it.
/// </summary>
public sealed record TestSpecification(
    ProgramKitIdentifier OwnerId,
    string Purpose,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<TestCategory> Categories,
    ImmutableArray<TestScenario> Scenarios,
    TestExecutionRequirements ExecutionRequirements,
    TestExpectedResult ExpectedResult,
    TestEvidenceShape EvidenceShape);

/// <summary>Selects one concrete, reproducible execution environment.</summary>
public sealed record ExecutionProfile(
    string RunnerClass,
    string Platform,
    ImmutableArray<string> EnvironmentAssumptions,
    ImmutableArray<ArtifactReference> DependencyClosure,
    TestExecutionAccessPolicy Access,
    TimeSpan Timeout,
    TestRetryPolicy Retry);

/// <summary>Binds an exact specification to an exact execution profile.</summary>
public sealed record TestSpecificationSelection(
    ArtifactReference Specification,
    ProfileReference Profile);

/// <summary>Identifies the outcome recorded by test evidence.</summary>
public enum TestEvidenceOutcome
{
    /// <summary>The expected result was observed.</summary>
    Passed,
    /// <summary>The expected result was not observed.</summary>
    Failed,
    /// <summary>The evidence cannot establish pass or failure.</summary>
    Inconclusive,
}

/// <summary>Records one typed observation without embedding an untyped JSON value.</summary>
public sealed record TestObservation(
    string Name,
    string Value,
    ArtifactReference? Attachment);

/// <summary>Binds observations to the exact specification, profile, and tested subject.</summary>
public sealed record TestEvidence(
    ArtifactReference Specification,
    ProfileReference Profile,
    ArtifactReference Subject,
    TestEvidenceOutcome Outcome,
    ImmutableArray<TestObservation> Observations,
    ProgramKitIdentifier ProducerId,
    DateTimeOffset ObservedAt,
    string CorrelationId);

/// <summary>Identifies whether independent review covers an artifact or a delta.</summary>
public enum IndependentReviewTargetKind
{
    /// <summary>Reviews one exact artifact revision.</summary>
    Artifact,
    /// <summary>Reviews the delta between two exact artifact revisions.</summary>
    Delta,
}

/// <summary>Identifies the independently reviewed artifact or exact delta.</summary>
public sealed record IndependentReviewTarget(
    IndependentReviewTargetKind Kind,
    ArtifactReference Artifact,
    ArtifactReference? BaseArtifact);

/// <summary>Records a reviewer's evidence-only conclusion.</summary>
public enum IndependentReviewDisposition
{
    /// <summary>The reviewer confirmed the selected claim.</summary>
    Confirmed,
    /// <summary>The reviewer recorded one or more concerns.</summary>
    ConcernRaised,
    /// <summary>The supplied evidence was insufficient for a conclusion.</summary>
    UnableToConclude,
}

/// <summary>
/// Records review performed by a principal other than the producer without implying approval authority.
/// </summary>
public sealed record IndependentReview(
    IndependentReviewTarget Target,
    ProgramKitIdentifier ProducerId,
    ProgramKitIdentifier ReviewerId,
    IndependentReviewDisposition Disposition,
    ImmutableArray<ArtifactReference> Evidence,
    string Summary,
    DateTimeOffset ReviewedAt);
