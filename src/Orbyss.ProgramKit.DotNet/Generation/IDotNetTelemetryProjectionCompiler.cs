using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Generates reviewed .NET diagnostics and OpenTelemetry host composition.</summary>
public interface IDotNetTelemetryProjectionCompiler
{
    /// <summary>Generates runtime source files for one host telemetry selection.</summary>
    ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host);

    /// <summary>Renders service-provider composition for one host.</summary>
    string RenderRegistration(DotNetHostDefinition host);

    /// <summary>Renders optional restrictive HTTP diagnostic middleware.</summary>
    string RenderMiddleware(DotNetHostDefinition host);
}
