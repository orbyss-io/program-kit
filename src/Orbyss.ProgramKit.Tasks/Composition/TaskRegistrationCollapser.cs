using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Diagnostics;

namespace Orbyss.ProgramKit.Tasks.Composition;

internal static class TaskRegistrationCollapser
{
    internal static ImmutableArray<TRegistration> Collapse<TRegistration>(
        ImmutableArray<TRegistration> registrations,
        Func<TRegistration, ArtifactReference> referenceSelector,
        Func<TRegistration, TRegistration, bool> exactEquals,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
        where TRegistration : class
    {
        if (registrations.IsDefault)
        {
            TaskDiagnostics.Add(
                diagnostics,
                TaskDiagnosticIds.InvalidRegistration,
                "An immutable registration collection must be initialized.",
                path);
            return [];
        }

        var result = ImmutableArray.CreateBuilder<TRegistration>();
        foreach (var group in registrations
                     .Select(
                         static (registration, index) =>
                             (Registration: registration, Index: index))
                     .GroupBy(
                         item => item.Registration is null
                             ? string.Concat("<null-", item.Index, ">")
                             : TaskRegistrationKey.Stable(
                                 referenceSelector(item.Registration)),
                         StringComparer.Ordinal)
                     .OrderBy(static group => group.Key, StringComparer.Ordinal))
        {
            var items = group.ToArray();
            var first = items[0].Registration;
            if (first is null)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "A registration is required.",
                    string.Concat(path, "/", items[0].Index));
                continue;
            }

            if (items.Skip(1).Any(item =>
                    item.Registration is null ||
                    !exactEquals(first, item.Registration)))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.ConflictingRegistration,
                    string.Concat(
                        "Stable registration identity '",
                        group.Key,
                        "' has conflicting exact registrations."),
                    path);
                continue;
            }

            result.Add(first);
        }

        return result.ToImmutable();
    }
}
