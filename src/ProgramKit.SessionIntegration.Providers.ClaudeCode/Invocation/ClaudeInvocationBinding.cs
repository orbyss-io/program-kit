using System;
using System.Collections.Generic;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Invocation;

public sealed record ClaudeCliInvocation(
    string Executable,
    IReadOnlyList<string> Arguments,
    string WorkingDirectory);

public static class ClaudeInvocationBinding
{
    private static readonly HashSet<string> FactoryOperations = new(StringComparer.Ordinal)
    {
        "explain",
        "construct",
        "evaluate",
    };

    private static readonly HashSet<string> SessionOperations = new(StringComparer.Ordinal)
    {
        "explain",
        "install",
        "verify",
        "remove",
    };

    public static ClaudeCliInvocation Factory(string executable, string operation, string workspace, string request)
    {
        Demand(executable, nameof(executable));
        Demand(workspace, nameof(workspace));
        Demand(request, nameof(request));
        if (!FactoryOperations.Contains(operation)) throw new ArgumentOutOfRangeException(nameof(operation));
        return new(executable, new[] { operation, "--workspace", workspace, "--request", request, "--format", "json" }, workspace);
    }

    public static ClaudeCliInvocation Session(string executable, string operation, string workspace, string request)
    {
        Demand(executable, nameof(executable));
        Demand(workspace, nameof(workspace));
        Demand(request, nameof(request));
        if (!SessionOperations.Contains(operation)) throw new ArgumentOutOfRangeException(nameof(operation));
        return new(executable, new[] { "session", operation, "--workspace", workspace, "--request", request, "--format", "json" }, workspace);
    }

    private static void Demand(string value, string name)
    {
        if (string.IsNullOrWhiteSpace(value) || value.Contains('\0')) throw new ArgumentException("A non-empty NUL-free value is required.", name);
    }
}
