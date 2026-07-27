using Orbyss.ProgramKit.Serialization.Json.Composition;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Registers the fixed local package and publish JSON profile.</summary>
public interface ILocalOperationsJsonProfileRegistration
{
    /// <summary>Adds the exact profile-owned metadata and converters.</summary>
    void Register(IProgramKitJsonBuilder builder);
}
