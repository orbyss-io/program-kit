using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Bindings;
using Orbyss.ProgramKit.Tasks.Core.Cancellation;
using Orbyss.ProgramKit.Tasks.Core.Definitions;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Instances;
using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Results;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Core.Validation;

/// <summary>Validates the complete Tasks.Core semantic contract family.</summary>
public interface ITaskContractValidator
{
    /// <summary>Validates a task definition.</summary>
    /// <param name="value">The definition to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskDefinition value);

    /// <summary>Validates a typed task request.</summary>
    /// <typeparam name="TRequest">The request payload type.</typeparam>
    /// <param name="value">The request to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate<TRequest>(TaskRequest<TRequest> value)
        where TRequest : notnull;

    /// <summary>Validates a task instance.</summary>
    /// <param name="value">The instance to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskInstance value);

    /// <summary>Validates a task attempt.</summary>
    /// <param name="value">The attempt to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskAttempt value);

    /// <summary>Validates an activation binding.</summary>
    /// <param name="value">The binding to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskActivationBinding value);

    /// <summary>Validates a task schedule definition.</summary>
    /// <param name="value">The schedule to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskScheduleDefinition value);

    /// <summary>Validates a task occurrence.</summary>
    /// <param name="value">The occurrence to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskOccurrence value);

    /// <summary>Validates a task lifecycle status view.</summary>
    /// <param name="value">The status view to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskInstanceStatus value);

    /// <summary>Validates a background-dispatch result.</summary>
    /// <param name="value">The dispatch result to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskDispatchResult value);

    /// <summary>Validates a typed successful response.</summary>
    /// <typeparam name="TResponse">The response payload type.</typeparam>
    /// <param name="value">The response to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate<TResponse>(TaskResponse<TResponse> value)
        where TResponse : notnull;

    /// <summary>Validates a task failure.</summary>
    /// <param name="value">The failure to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskFailure value);

    /// <summary>Validates a typed immediate-execution outcome.</summary>
    /// <typeparam name="TResponse">The response payload type.</typeparam>
    /// <param name="value">The outcome to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate<TResponse>(
        TaskExecutionOutcome<TResponse> value)
        where TResponse : notnull;

    /// <summary>Validates an explicit cancellation request.</summary>
    /// <param name="value">The cancellation request to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskCancellationRequest value);

    /// <summary>Validates a cancellation-request result.</summary>
    /// <param name="value">The cancellation result to validate.</param>
    /// <returns>The complete validation result.</returns>
    ProgramKitValidationResult Validate(TaskCancellationResult value);
}
