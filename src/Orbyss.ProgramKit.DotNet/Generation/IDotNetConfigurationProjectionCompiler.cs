using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Reusable design-time compiler for owner-authored configuration definitions.</summary>
public interface IDotNetConfigurationProjectionCompiler
{
    /// <summary>Compiles deterministic source, configuration artifacts, reports, and provenance.</summary>
    ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host);

    /// <summary>Renders exact provider and Options registrations for host composition.</summary>
    string RenderRegistration(DotNetHostDefinition host);
}
