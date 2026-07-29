using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

namespace Orbyss.ProgramKit.CommandLine.Operations.Help;

/// <summary>Renders deterministic help from the finite command descriptors.</summary>
public interface ICommandHelpRenderer
{
    /// <summary>Renders concise first-use guidance and the complete command catalog.</summary>
    byte[] RenderTopLevel(bool firstUse);

    /// <summary>Resolves and renders one exact command path.</summary>
    byte[] RenderCommandPath(IReadOnlyList<string> path);

    /// <summary>Renders one exact descriptor in the selected representation.</summary>
    byte[] RenderDescriptor(CommandDescriptor descriptor, string format);
}
