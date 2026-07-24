using Orbyss.ProgramKit.Serialization.Json.Composition;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Registers the fixed non-extensible DotNet shell bootstrap profile.</summary>
public interface IDotNetJsonProfileRegistration
{
    /// <summary>Adds the exact owned profile and source-generated metadata.</summary>
    void Register(IProgramKitJsonBuilder builder);
}
