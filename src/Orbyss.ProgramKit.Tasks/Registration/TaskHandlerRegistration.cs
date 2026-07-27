using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Attempts;
using Orbyss.ProgramKit.Tasks.Core.Execution;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Typed registration bridge for one consumer-owned handler.</summary>
public sealed class TaskHandlerRegistration<TRequest, TResponse, THandler> :
    ITaskHandlerRegistration
    where TRequest : notnull
    where TResponse : notnull
    where THandler : class, ITaskHandler<TRequest, TResponse>
{
    /// <summary>Initializes an exact typed handler registration.</summary>
    public TaskHandlerRegistration(
        ArtifactReference handlerRevision,
        SemanticVersionRange supportedDefinitionVersions)
    {
        HandlerRevision = handlerRevision ??
            throw new ArgumentNullException(nameof(handlerRevision));
        SupportedDefinitionVersions = supportedDefinitionVersions;
    }

    /// <inheritdoc />
    public ArtifactReference HandlerRevision { get; }

    /// <inheritdoc />
    public SemanticVersionRange SupportedDefinitionVersions { get; }

    /// <inheritdoc />
    public Type RequestType => typeof(TRequest);

    /// <inheritdoc />
    public Type ResponseType => typeof(TResponse);

    /// <inheritdoc />
    public Type HandlerType => typeof(THandler);

    /// <inheritdoc />
    public async ValueTask<object> InvokeAsync(
        IServiceProvider services,
        TaskHandlerContext context,
        object request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(context);
        if (request is not TRequest typedRequest)
        {
            throw new ArgumentException(
                string.Concat(
                    "The request payload must be assignable to ",
                    typeof(TRequest).FullName,
                    "."),
                nameof(request));
        }

        var handler = services.GetRequiredService<THandler>();
        var response = await handler
            .HandleAsync(context, typedRequest, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }
}
