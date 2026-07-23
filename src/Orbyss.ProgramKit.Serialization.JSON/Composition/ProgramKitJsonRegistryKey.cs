using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal static class ProgramKitJsonRegistryKey
{
    internal static string Exact(JsonSerializationProfileRef reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    internal static string Exact(ProfileReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    internal static string Revision(JsonSerializationProfileRef reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    internal static string Revision(JsonSerializationContributionRef reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);
}
