using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Tasks.Diagnostics;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

internal static class TaskMiddlewareOrderer
{
    internal static ImmutableArray<TaskMiddlewareRegistration> Order(
        ImmutableArray<TaskMiddlewareRegistration> registrations,
        TaskMiddlewarePhase phase,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var selected = registrations
            .Where(registration => registration.Phase == phase)
            .ToArray();
        var byIdentity = selected.ToDictionary(
            registration => registration.Revision.Identity.Value,
            StringComparer.Ordinal);
        var outgoing = byIdentity.Keys.ToDictionary(
            static identity => identity,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        var incoming = byIdentity.Keys.ToDictionary(
            static identity => identity,
            static _ => 0,
            StringComparer.Ordinal);

        foreach (var registration in selected)
        {
            foreach (var later in registration.Before)
            {
                AddEdge(
                    registration.Revision.Identity.Value,
                    later.Value,
                    byIdentity,
                    outgoing,
                    incoming,
                    diagnostics);
            }

            foreach (var earlier in registration.After)
            {
                AddEdge(
                    earlier.Value,
                    registration.Revision.Identity.Value,
                    byIdentity,
                    outgoing,
                    incoming,
                    diagnostics);
            }
        }

        if (diagnostics.Any(static diagnostic =>
                diagnostic.Id == TaskDiagnosticIds.InvalidMiddlewareOrder))
        {
            return [];
        }

        var available = selected
            .Where(registration =>
                incoming[registration.Revision.Identity.Value] == 0)
            .ToList();
        var ordered =
            ImmutableArray.CreateBuilder<TaskMiddlewareRegistration>();
        while (available.Count > 0)
        {
            available.Sort(Compare);
            var next = available[0];
            available.RemoveAt(0);
            ordered.Add(next);
            foreach (var dependent in outgoing[
                         next.Revision.Identity.Value]
                     .Order(StringComparer.Ordinal))
            {
                incoming[dependent]--;
                if (incoming[dependent] == 0)
                {
                    available.Add(byIdentity[dependent]);
                }
            }
        }

        if (ordered.Count != selected.Length)
        {
            TaskDiagnostics.Add(
                diagnostics,
                TaskDiagnosticIds.InvalidMiddlewareOrder,
                "Task middleware ordering contains a cycle.",
                "/middleware");
            return [];
        }

        return ordered.ToImmutable();
    }

    private static void AddEdge(
        string earlier,
        string later,
        Dictionary<string, TaskMiddlewareRegistration> registrations,
        Dictionary<string, HashSet<string>> outgoing,
        Dictionary<string, int> incoming,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!registrations.ContainsKey(earlier) ||
            !registrations.ContainsKey(later))
        {
            TaskDiagnostics.Add(
                diagnostics,
                TaskDiagnosticIds.InvalidMiddlewareOrder,
                string.Concat(
                    "Middleware ordering references an unknown identity: ",
                    earlier,
                    " -> ",
                    later,
                    "."),
                "/middleware");
            return;
        }

        if (outgoing[earlier].Add(later))
        {
            incoming[later]++;
        }
    }

    private static int Compare(
        TaskMiddlewareRegistration left,
        TaskMiddlewareRegistration right)
    {
        var priority = left.Priority.CompareTo(right.Priority);
        return priority != 0
            ? priority
            : StringComparer.Ordinal.Compare(
                left.Revision.Identity.Value,
                right.Revision.Identity.Value);
    }
}
