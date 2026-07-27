using Orbyss.ProgramKit.Artifacts.Primitives;

namespace ObservatoryScheduling.Core.Configuration;

/// <summary>Stable fictional JSON-profile selection for the fixture contracts.</summary>
public static class ObservatoryJsonProfile
{
    /// <summary>Gets the profile identity.</summary>
    public static ProgramKitIdentifier Identity { get; } =
        new("pkid:profile:fixture:observatory-json");

    /// <summary>Gets the supported profile range.</summary>
    public static SemanticVersionRange Range { get; } = new("[1.0.0,2.0.0)");
}
