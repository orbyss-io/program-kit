using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Canonicalization;

internal struct CanonicalizationState
{
    internal CanonicalizationState(JsonSerializationLimits limits)
    {
        Limits = limits;
        TokenCount = 0;
    }

    internal JsonSerializationLimits Limits { get; }

    internal long TokenCount { get; set; }
}
