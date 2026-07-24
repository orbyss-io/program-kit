using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Bindings;
using Orbyss.ProgramKit.Tasks.Core.Cancellation;
using Orbyss.ProgramKit.Tasks.Core.Definitions;
using Orbyss.ProgramKit.Tasks.Core.Diagnostics;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Results;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Core.Validation;

/// <summary>Default deterministic validator for Tasks.Core contracts.</summary>
public sealed class TaskContractValidator : ITaskContractValidator
{
    private readonly IProgramKitSemanticValidator<ArtifactReference> referenceValidator;

    /// <summary>Initializes a Tasks.Core contract validator.</summary>
    /// <param name="referenceValidator">The injected artifact-reference validator.</param>
    public TaskContractValidator(
        IProgramKitSemanticValidator<ArtifactReference> referenceValidator)
    {
        this.referenceValidator = referenceValidator ??
            throw new ArgumentNullException(nameof(referenceValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskDefinition value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskDefinition,
                "A task definition is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-definition",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskDefinition);
        AddResult(diagnostics, ProgramKitIdentifier.Validate(value.Owner.Value, "/owner"));
        ValidateReferenceSet(
            diagnostics,
            (value.RequestContract, "/requestContract"),
            (value.ResponseContract, "/responseContract"),
            (value.FailureContract, "/failureContract"),
            (value.AuthorityPolicy, "/authorityPolicy"),
            (value.CancellationPolicy, "/cancellationPolicy"),
            (value.IdempotencyPolicy, "/idempotencyPolicy"),
            (value.RetryPolicy, "/retryPolicy"),
            (value.ObservabilityPolicy, "/observabilityPolicy"),
            (value.ResourcePolicy, "/resourcePolicy"));
        RequireKinds(
            diagnostics,
            TasksCoreDiagnosticIds.InvalidTaskDefinition,
            "contract",
            (value.RequestContract, "/requestContract"),
            (value.ResponseContract, "/responseContract"),
            (value.FailureContract, "/failureContract"));
        RequireKinds(
            diagnostics,
            TasksCoreDiagnosticIds.InvalidTaskDefinition,
            "policy",
            (value.AuthorityPolicy, "/authorityPolicy"),
            (value.CancellationPolicy, "/cancellationPolicy"),
            (value.IdempotencyPolicy, "/idempotencyPolicy"),
            (value.RetryPolicy, "/retryPolicy"),
            (value.ObservabilityPolicy, "/observabilityPolicy"),
            (value.ResourcePolicy, "/resourcePolicy"));
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate<TRequest>(TaskRequest<TRequest> value)
        where TRequest : notnull
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskRequest,
                "A task request is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-request",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskRequest);
        ValidateReferenceSet(
            diagnostics,
            (value.DefinitionRevision, "/definitionRevision"),
            (value.RequestContract, "/requestContract"),
            (value.ResponseContract, "/responseContract"),
            (value.FailureContract, "/failureContract"));
        RequireKind(
            diagnostics,
            value.DefinitionRevision,
            "task-definition",
            "/definitionRevision",
            TasksCoreDiagnosticIds.InvalidTaskRequest);
        AddResult(
            diagnostics,
            ProgramKitIdentifier.Validate(value.RequestedBy.Value, "/requestedBy"));
        if (value.Payload is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskRequest,
                "A typed request payload is required.",
                "/payload");
        }

        if (value.IdempotencyKey is not null &&
            string.IsNullOrWhiteSpace(value.IdempotencyKey))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskRequest,
                "An idempotency key must be non-empty when supplied.",
                "/idempotencyKey");
        }

        ValidateReferences(
            diagnostics,
            value.CausalReferences,
            "/causalReferences",
            TasksCoreDiagnosticIds.InvalidTaskRequest);
        ValidateOptionalReference(
            diagnostics,
            value.OccurrenceRevision,
            "/occurrenceRevision");
        RequireKind(
            diagnostics,
            value.OccurrenceRevision,
            "task-occurrence",
            "/occurrenceRevision",
            TasksCoreDiagnosticIds.InvalidTaskRequest);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskInstance value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskInstance,
                "A task instance is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-instance",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskInstance);
        ValidateReferenceSet(
            diagnostics,
            (value.RequestRevision, "/requestRevision"),
            (value.DefinitionRevision, "/definitionRevision"),
            (value.RequestContract, "/requestContract"),
            (value.ResponseContract, "/responseContract"),
            (value.FailureContract, "/failureContract"));
        RequireKind(
            diagnostics,
            value.RequestRevision,
            "task-request",
            "/requestRevision",
            TasksCoreDiagnosticIds.InvalidTaskInstance);
        RequireKind(
            diagnostics,
            value.DefinitionRevision,
            "task-definition",
            "/definitionRevision",
            TasksCoreDiagnosticIds.InvalidTaskInstance);
        if (value.IdempotencyKey is not null &&
            string.IsNullOrWhiteSpace(value.IdempotencyKey))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskInstance,
                "An accepted idempotency key must be non-empty when supplied.",
                "/idempotencyKey");
        }

        ValidateOptionalReference(
            diagnostics,
            value.OccurrenceRevision,
            "/occurrenceRevision");
        RequireKind(
            diagnostics,
            value.OccurrenceRevision,
            "task-occurrence",
            "/occurrenceRevision",
            TasksCoreDiagnosticIds.InvalidTaskInstance);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskAttempt value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskAttempt,
                "A task attempt is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-attempt",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskAttempt);
        ValidateReferenceSet(
            diagnostics,
            (value.InstanceRevision, "/instanceRevision"),
            (value.ActivationBindingRevision, "/activationBindingRevision"));
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskAttempt);
        RequireKind(
            diagnostics,
            value.ActivationBindingRevision,
            "task-activation-binding",
            "/activationBindingRevision",
            TasksCoreDiagnosticIds.InvalidTaskAttempt);
        if (!Enum.IsDefined(value.State))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskAttempt,
                "The task attempt state is not defined.",
                "/state");
        }
        if (value.Number <= 0)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskAttempt,
                "An attempt number must be positive.",
                "/number");
        }

        var terminal = value.State is TaskAttemptState.Succeeded or
            TaskAttemptState.Failed or
            TaskAttemptState.Cancelled;
        if (terminal != value.CompletedAt.HasValue ||
            (value.CompletedAt.HasValue &&
             value.CompletedAt.Value < value.StartedAt))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskAttempt,
                "Only terminal attempts have a completion instant, not before their start.",
                "/completedAt");
        }

        if ((value.State == TaskAttemptState.Failed) !=
            (value.FailureRevision is not null))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskAttempt,
                "Exactly failed attempts require a failure revision.",
                "/failureRevision");
        }

        ValidateOptionalReference(
            diagnostics,
            value.FailureRevision,
            "/failureRevision");
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskActivationBinding value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskActivationBinding,
                "A task activation binding is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-activation-binding",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskActivationBinding);
        ValidateReferenceSet(
            diagnostics,
            (value.DefinitionRevision, "/definitionRevision"),
            (value.HandlerRevision, "/handlerRevision"),
            (value.OwningFeatureRevision, "/owningFeatureRevision"),
            (value.RuntimeRevision, "/runtimeRevision"),
            (value.RetryPolicyRevision, "/retryPolicyRevision"),
            (value.IdempotencyPolicyRevision, "/idempotencyPolicyRevision"));
        RequireKind(
            diagnostics,
            value.DefinitionRevision,
            "task-definition",
            "/definitionRevision",
            TasksCoreDiagnosticIds.InvalidTaskActivationBinding);
        AddResult(
            diagnostics,
            ProgramKitIdentifier.Validate(
                value.ActivationIdentity.Value,
                "/activationIdentity"));
        ValidateReferences(
            diagnostics,
            value.MiddlewareRevisions,
            "/middlewareRevisions",
            TasksCoreDiagnosticIds.InvalidTaskActivationBinding);
        var scheduledFieldCount = CountNotNull(
            value.ScheduleRevision,
            value.MisfirePolicyRevision,
            value.OverlapPolicyRevision);
        if (scheduledFieldCount is not 0 and not 3)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskActivationBinding,
                "Schedule, misfire, and overlap selections must be supplied together.",
                "/scheduleRevision");
        }

        ValidateOptionalReference(diagnostics, value.ScheduleRevision, "/scheduleRevision");
        RequireKind(
            diagnostics,
            value.ScheduleRevision,
            "task-schedule-definition",
            "/scheduleRevision",
            TasksCoreDiagnosticIds.InvalidTaskActivationBinding);
        ValidateOptionalReference(
            diagnostics,
            value.MisfirePolicyRevision,
            "/misfirePolicyRevision");
        ValidateOptionalReference(
            diagnostics,
            value.OverlapPolicyRevision,
            "/overlapPolicyRevision");
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskScheduleDefinition value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition,
                "A task schedule definition is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-schedule-definition",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition);
        ValidateReferenceSet(
            diagnostics,
            (value.DefinitionRevision, "/definitionRevision"),
            (value.ActivationBindingRevision, "/activationBindingRevision"),
            (value.DescriptorRevision, "/descriptorRevision"),
            (value.DescriptorSchema, "/descriptorSchema"),
            (value.OccurrenceCalculatorProfile, "/occurrenceCalculatorProfile"));
        RequireKind(
            diagnostics,
            value.DefinitionRevision,
            "task-definition",
            "/definitionRevision",
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition);
        RequireKind(
            diagnostics,
            value.ActivationBindingRevision,
            "task-activation-binding",
            "/activationBindingRevision",
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition);
        RequireKind(
            diagnostics,
            value.DescriptorSchema,
            "schema",
            "/descriptorSchema",
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition);
        RequireKind(
            diagnostics,
            value.OccurrenceCalculatorProfile,
            "profile",
            "/occurrenceCalculatorProfile",
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskOccurrence value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskOccurrence,
                "A task occurrence is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-occurrence",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskOccurrence);
        ValidateReferenceSet(
            diagnostics,
            (value.ScheduleRevision, "/scheduleRevision"),
            (value.DefinitionRevision, "/definitionRevision"),
            (value.DescriptorRevision, "/descriptorRevision"),
            (value.OccurrenceCalculatorProfile, "/occurrenceCalculatorProfile"));
        RequireKind(
            diagnostics,
            value.ScheduleRevision,
            "task-schedule-definition",
            "/scheduleRevision",
            TasksCoreDiagnosticIds.InvalidTaskOccurrence);
        RequireKind(
            diagnostics,
            value.DefinitionRevision,
            "task-definition",
            "/definitionRevision",
            TasksCoreDiagnosticIds.InvalidTaskOccurrence);
        RequireKind(
            diagnostics,
            value.OccurrenceCalculatorProfile,
            "profile",
            "/occurrenceCalculatorProfile",
            TasksCoreDiagnosticIds.InvalidTaskOccurrence);
        if (value.Sequence < 0)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskOccurrence,
                "An occurrence sequence cannot be negative.",
                "/sequence");
        }

        if (value.ScheduledFor > value.EvaluatedAt)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskOccurrence,
                "A calculated occurrence cannot be later than its evaluation instant.",
                "/scheduledFor");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskInstanceStatus value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task status is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateReference(
            diagnostics,
            value.InstanceRevision,
            "/instanceRevision");
        ValidateOptionalReference(
            diagnostics,
            value.LatestAttemptRevision,
            "/latestAttemptRevision");
        ValidateOptionalReference(
            diagnostics,
            value.TerminalOutcomeRevision,
            "/terminalOutcomeRevision");
        if (!Enum.IsDefined(value.State))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "The task instance state is not defined.",
                "/state");
        }
        if (value.AttemptCount < 0 ||
            (value.IsTerminal != (value.TerminalOutcomeRevision is not null)))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "Status requires a non-negative attempt count and exactly terminal states require an outcome.",
                "/state");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskDispatchResult value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task dispatch result is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateReference(diagnostics, value.RequestRevision, "/requestRevision");
        RequireKind(
            diagnostics,
            value.RequestRevision,
            "task-request",
            "/requestRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        ValidateOptionalReference(
            diagnostics,
            value.InstanceRevision,
            "/instanceRevision");
        var accepted = value.Disposition == TaskDispatchDisposition.Accepted;
        if (!Enum.IsDefined(value.Disposition) ||
            accepted != (value.InstanceRevision is not null))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "Exactly accepted dispatches require an instance revision.",
                "/disposition");
        }

        ValidateDiagnostics(diagnostics, value.Diagnostics, "/diagnostics");
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate<TResponse>(
        TaskResponse<TResponse> value)
        where TResponse : notnull
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task response is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-response",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        ValidateReference(diagnostics, value.InstanceRevision, "/instanceRevision");
        ValidateReference(diagnostics, value.ResponseContract, "/responseContract");
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        RequireKind(
            diagnostics,
            value.ResponseContract,
            "contract",
            "/responseContract",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        if (value.Payload is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A typed response payload is required.",
                "/payload");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskFailure value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task failure is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-failure",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        ValidateReference(diagnostics, value.InstanceRevision, "/instanceRevision");
        ValidateReference(diagnostics, value.FailureContract, "/failureContract");
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        RequireKind(
            diagnostics,
            value.FailureContract,
            "contract",
            "/failureContract",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        if (string.IsNullOrWhiteSpace(value.Code))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A stable failure code is required.",
                "/code");
        }

        ValidateReferences(
            diagnostics,
            value.EvidenceReferences,
            "/evidenceReferences",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate<TResponse>(
        TaskExecutionOutcome<TResponse> value)
        where TResponse : notnull
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task execution outcome is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateReference(diagnostics, value.RequestRevision, "/requestRevision");
        ValidateOptionalReference(
            diagnostics,
            value.InstanceRevision,
            "/instanceRevision");
        RequireKind(
            diagnostics,
            value.RequestRevision,
            "task-request",
            "/requestRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        if (!Enum.IsDefined(value.Kind) ||
            !HasValidOutcomeShape(value))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "The execution outcome kind, instance, response, and failure are inconsistent.",
                "/kind");
        }

        if (value.Response is not null)
        {
            AddResult(diagnostics, Validate(value.Response));
        }

        if (value.Failure is not null)
        {
            AddResult(diagnostics, Validate(value.Failure));
        }

        ValidateDiagnostics(diagnostics, value.Diagnostics, "/diagnostics");
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskCancellationRequest value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task cancellation request is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateRevision(
            diagnostics,
            value.Revision,
            "task-cancellation-request",
            "/revision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        ValidateReference(diagnostics, value.InstanceRevision, "/instanceRevision");
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        AddResult(
            diagnostics,
            ProgramKitIdentifier.Validate(
                value.RequestedBy.Value,
                "/requestedBy"));
        if (string.IsNullOrWhiteSpace(value.ReasonCode))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A stable cancellation reason code is required.",
                "/reasonCode");
        }

        ValidateReferences(
            diagnostics,
            value.CausalReferences,
            "/causalReferences",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TaskCancellationResult value)
    {
        var diagnostics = CreateDiagnostics();
        if (value is null)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "A task cancellation result is required.",
                string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateReference(
            diagnostics,
            value.CancellationRequestRevision,
            "/cancellationRequestRevision");
        RequireKind(
            diagnostics,
            value.CancellationRequestRevision,
            "task-cancellation-request",
            "/cancellationRequestRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        ValidateReference(diagnostics, value.InstanceRevision, "/instanceRevision");
        RequireKind(
            diagnostics,
            value.InstanceRevision,
            "task-instance",
            "/instanceRevision",
            TasksCoreDiagnosticIds.InvalidTaskLifecycleView);
        if (!Enum.IsDefined(value.Disposition))
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "The cancellation disposition is not defined.",
                "/disposition");
        }

        ValidateDiagnostics(diagnostics, value.Diagnostics, "/diagnostics");
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static ImmutableArray<ProgramKitDiagnostic>.Builder CreateDiagnostics() =>
        ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();

    private static void AddError(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string id,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                id,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));

    private static void AddResult(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitValidationResult result) =>
        diagnostics.AddRange(result.Diagnostics);

    private static void ValidateDiagnostics(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ImmutableArray<ProgramKitDiagnostic> values,
        string path)
    {
        if (values.IsDefault)
        {
            AddError(
                diagnostics,
                TasksCoreDiagnosticIds.InvalidTaskLifecycleView,
                "An immutable diagnostic collection must be initialized.",
                path);
        }
    }

    private void ValidateRevision(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ArtifactReference? reference,
        string kind,
        string path,
        string diagnosticId)
    {
        ValidateReference(diagnostics, reference, path);
        RequireKind(diagnostics, reference, kind, path, diagnosticId);
    }

    private void ValidateReferenceSet(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        params (ArtifactReference? Reference, string Path)[] references)
    {
        foreach (var item in references)
        {
            ValidateReference(diagnostics, item.Reference, item.Path);
        }
    }

    private void ValidateReferences(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ImmutableArray<ArtifactReference> references,
        string path,
        string diagnosticId)
    {
        if (references.IsDefault)
        {
            AddError(
                diagnostics,
                diagnosticId,
                "An immutable reference collection must be initialized.",
                path);
            return;
        }

        var exactKeys = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < references.Length; index++)
        {
            var itemPath = string.Concat(path, "/", index);
            var reference = references[index];
            ValidateReference(diagnostics, reference, itemPath);
            if (reference is not null &&
                !exactKeys.Add(ExactKey(reference)))
            {
                AddError(
                    diagnostics,
                    diagnosticId,
                    "Duplicate exact references are forbidden.",
                    itemPath);
            }
        }
    }

    private void ValidateOptionalReference(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ArtifactReference? reference,
        string path)
    {
        if (reference is not null)
        {
            ValidateReference(diagnostics, reference, path);
        }
    }

    private void ValidateReference(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ArtifactReference? reference,
        string path)
    {
        if (reference is null)
        {
            AddError(
                diagnostics,
                ArtifactDiagnosticIds.InvalidArtifactReference,
                "An exact artifact reference is required.",
                path);
            return;
        }

        var result = referenceValidator.Validate(reference);
        foreach (var diagnostic in result.Diagnostics)
        {
            diagnostics.Add(diagnostic with
            {
                Path = string.Concat(path, diagnostic.Path),
            });
        }
    }

    private static void RequireKind(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ArtifactReference? reference,
        string expectedKind,
        string path,
        string diagnosticId)
    {
        if (reference is not null &&
            !string.Equals(
                reference.Identity.Kind,
                expectedKind,
                StringComparison.Ordinal))
        {
            AddError(
                diagnostics,
                diagnosticId,
                string.Concat(
                    "The reference identity kind must be '",
                    expectedKind,
                    "'."),
                string.Concat(path, "/identity"));
        }
    }

    private static void RequireKinds(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string diagnosticId,
        string expectedKind,
        params (ArtifactReference? Reference, string Path)[] references)
    {
        foreach (var item in references)
        {
            RequireKind(
                diagnostics,
                item.Reference,
                expectedKind,
                item.Path,
                diagnosticId);
        }
    }

    private static bool HasValidOutcomeShape<TResponse>(
        TaskExecutionOutcome<TResponse> value)
        where TResponse : notnull =>
        value.Kind switch
        {
            TaskExecutionOutcomeKind.Rejected or
                TaskExecutionOutcomeKind.CancelledBeforeAcceptance =>
                value.InstanceRevision is null &&
                value.Response is null &&
                value.Failure is null,
            TaskExecutionOutcomeKind.Succeeded =>
                value.InstanceRevision is not null &&
                value.Response is not null &&
                value.Response.InstanceRevision == value.InstanceRevision &&
                value.Failure is null,
            TaskExecutionOutcomeKind.Failed =>
                value.InstanceRevision is not null &&
                value.Response is null &&
                value.Failure is not null &&
                value.Failure.InstanceRevision == value.InstanceRevision,
            TaskExecutionOutcomeKind.Cancelled =>
                value.InstanceRevision is not null &&
                value.Response is null &&
                value.Failure is null,
            _ => false,
        };

    private static int CountNotNull(
        ArtifactReference? first,
        ArtifactReference? second,
        ArtifactReference? third) =>
        (first is null ? 0 : 1) +
        (second is null ? 0 : 1) +
        (third is null ? 0 : 1);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
