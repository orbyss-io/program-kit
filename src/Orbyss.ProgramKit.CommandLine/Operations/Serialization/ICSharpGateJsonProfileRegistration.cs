using Orbyss.ProgramKit.Serialization.Json.Composition;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Registers the closed C# build-gate command JSON profile.</summary>
public interface ICSharpGateJsonProfileRegistration
{
    /// <summary>Adds exact source-generated metadata and enum converters.</summary>
    void Register(IProgramKitJsonBuilder builder);
}
