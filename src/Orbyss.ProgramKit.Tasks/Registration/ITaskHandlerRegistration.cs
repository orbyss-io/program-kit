using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Attempts;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Runtime-neutral bridge for one typed consumer-owned task handler.</summary>
public interface ITaskHandlerRegistration
{
    /// <summary>Gets the exact handler identity.</summary>
    ArtifactReference HandlerRevision { get; }

    /// <summary>Gets the compatible task-definition range.</summary>
    SemanticVersionRange SupportedDefinitionVersions { get; }

    /// <summary>Gets the typed request model.</summary>
    Type RequestType { get; }

    /// <summary>Gets the typed response model.</summary>
    Type ResponseType { get; }

    /// <summary>Gets the consumer-owned handler implementation type.</summary>
    Type HandlerType { get; }

    /// <summary>Invokes the typed handler through an exact activation scope.</summary>
    ValueTask<object> InvokeAsync(
        IServiceProvider services,
        TaskHandlerContext context,
        object request,
        CancellationToken cancellationToken);
}
