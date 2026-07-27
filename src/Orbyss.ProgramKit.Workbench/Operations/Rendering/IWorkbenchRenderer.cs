namespace Orbyss.ProgramKit.Workbench.Operations.Rendering;

/// <summary>Renders one validated model as deterministic Markdown.</summary>
/// <typeparam name="T">The structured source model.</typeparam>
public interface IWorkbenchRenderer<in T>
{
    /// <summary>Renders culture-invariant Markdown.</summary>
    string RenderMarkdown(T value);
}
