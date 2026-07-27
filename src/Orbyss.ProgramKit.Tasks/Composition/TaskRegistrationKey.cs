using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Composition;

internal static class TaskRegistrationKey
{
    internal static string Stable(ArtifactReference reference) =>
        reference.Identity.Value;

    internal static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
