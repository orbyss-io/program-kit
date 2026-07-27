using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.Diagnostics;
using Orbyss.ProgramKit.Modularity.InProcess.Diagnostics;

namespace Orbyss.ProgramKit.Modularity.InProcess.Contributions;

/// <summary>
/// Deterministically publishes domain contributions to an immutable registry
/// in the current process and call stack.
/// </summary>
/// <remarks>
/// Execution is sequential and reentrant. This implementation has no queue,
/// persistence, retry, replay, outbox, transaction, or cross-process behavior.
/// </remarks>
public sealed class InProcessDomainContributionPublisher : IDomainContributionPublisher
{
    private readonly IDomainContributionRegistry registry;

    /// <summary>Initializes the publisher with one frozen explicit registry.</summary>
    /// <param name="registry">The complete handler registry selected by the host.</param>
    public InProcessDomainContributionPublisher(IDomainContributionRegistry registry)
    {
        ArgumentNullException.ThrowIfNull(registry);
        this.registry = registry;
    }

    /// <inheritdoc />
    public async ValueTask<DomainContributionPublicationResult> PublishAsync<TContribution>(
        TContribution contribution,
        DomainContributionPublicationPolicy policy,
        CancellationToken cancellationToken = default)
        where TContribution : IDomainContribution
    {
        ArgumentNullException.ThrowIfNull(contribution);
        ArgumentNullException.ThrowIfNull(policy);
        ValidatePolicy(policy);
        cancellationToken.ThrowIfCancellationRequested();

        var handlers = registry.GetRegistrations<TContribution>();
        if (handlers.IsDefaultOrEmpty)
        {
            return DomainContributionPublicationResult.Empty;
        }

        var executions =
            ImmutableArray.CreateBuilder<DomainContributionHandlerExecution>(handlers.Length);
        for (var index = 0; index < handlers.Length; index++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var registration = handlers[index];
            try
            {
                await registration
                    .InvokeAsync(contribution, cancellationToken)
                    .ConfigureAwait(false);
                cancellationToken.ThrowIfCancellationRequested();
                executions.Add(new DomainContributionHandlerExecution(
                    registration.Descriptor.Registration,
                    DomainContributionHandlerExecutionStatus.Succeeded,
                    null,
                    null));
            }
            catch (OperationCanceledException exception)
            {
                cancellationToken.ThrowIfCancellationRequested();
                if (policy.Cancellation !=
                    DomainContributionCancellationPolicy
                        .TreatUnrequestedCancellationAsFailure)
                {
                    throw;
                }

                HandleFailure(
                    registration,
                    exception,
                    index,
                    policy,
                    executions);
            }
            catch (Exception exception)
                when (ModularityExceptionBoundary.IsNonFatal(exception))
            {
                cancellationToken.ThrowIfCancellationRequested();
                HandleFailure(
                    registration,
                    exception,
                    index,
                    policy,
                    executions);
            }
        }

        cancellationToken.ThrowIfCancellationRequested();
        return new DomainContributionPublicationResult(executions.MoveToImmutable());
    }

    private static void ValidatePolicy(DomainContributionPublicationPolicy policy)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (!Enum.IsDefined(policy.Failure))
        {
            diagnostics.Add(Error(
                "Publication failure policy must be a defined value.",
                "/policy/failure"));
        }

        if (!Enum.IsDefined(policy.Cancellation))
        {
            diagnostics.Add(Error(
                "Publication cancellation policy must be a defined value.",
                "/policy/cancellation"));
        }

        if (diagnostics.Count > 0)
        {
            throw new ModularityValidationException(
                "The domain-contribution publication policy is invalid.",
                ProgramKitValidationResult.From(diagnostics));
        }
    }

    private static void HandleFailure(
        DomainContributionHandlerRegistration registration,
        Exception exception,
        int index,
        DomainContributionPublicationPolicy policy,
        ImmutableArray<DomainContributionHandlerExecution>.Builder executions)
    {
        var diagnostic = new ProgramKitDiagnostic(
            ModularityDiagnosticIds.ContributionHandlerFailure,
            ProgramKitDiagnosticSeverity.Error,
            string.Concat(
                "Domain-contribution handler '",
                registration.Descriptor.Registration.Identity.Value,
                "' failed."),
            string.Concat("/handlers/", index));
        executions.Add(new DomainContributionHandlerExecution(
            registration.Descriptor.Registration,
            DomainContributionHandlerExecutionStatus.Failed,
            diagnostic,
            exception));

        if (policy.Failure == DomainContributionFailurePolicy.FailFast)
        {
            var result =
                new DomainContributionPublicationResult(executions.ToImmutable());
            throw new DomainContributionPublicationException(
                result,
                registration.Descriptor.Registration,
                diagnostic,
                exception);
        }
    }

    private static ProgramKitDiagnostic Error(string message, string path) =>
        new(
            ModularityDiagnosticIds.InvalidPublicationPolicy,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path);
}
