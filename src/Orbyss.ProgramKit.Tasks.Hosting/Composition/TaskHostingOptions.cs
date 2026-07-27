namespace Orbyss.ProgramKit.Tasks.Hosting.Composition;

/// <summary>Explicit Generic Host shutdown behavior for the task runtime.</summary>
public sealed record TaskHostingOptions
{
    /// <summary>Gets or initializes whether shutdown drains accepted queued work.</summary>
    public bool DrainOnShutdown { get; init; } = true;
}
