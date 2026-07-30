using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

internal static class ReleaseBindingFixtureValidator
{
    public static string? FindViolation(JsonElement fixture)
    {
        var facts = fixture.GetProperty("facts");
        return fixture.GetProperty("kind").GetString() switch
        {
            "valid-release-binding" => ValidateCompleteBinding(facts),
            "random-compiler-receipt" =>
                facts.GetProperty("receiptContainsRandomData").GetBoolean() ||
                ValuesDiffer(facts, "firstAssemblyDigest", "secondAssemblyDigest")
                    ? "stable-compiler-output"
                    : null,
            "absolute-root-leakage" =>
                !facts.GetProperty("pathMapApplied").GetBoolean() ||
                ValuesDiffer(facts, "firstAssemblyDigest", "secondAssemblyDigest")
                    ? "checkout-root-normalization"
                    : null,
            "nondeterministic-package-metadata" =>
                ValuesDiffer(facts, "firstPackageDigest", "secondPackageDigest") ||
                ValuesDiffer(facts, "firstEntryTimestamp", "secondEntryTimestamp")
                    ? "package-byte-reproducibility"
                    : null,
            "placeholder-selection" =>
                !HasCanonicalDigest(facts, "packageSha256") ||
                !HasCanonicalDigest(facts, "assemblyDigest")
                    ? "canonical-selection-concreteness"
                    : null,
            "release-path-divergence" =>
                ValuesDiffer(facts, "manifestPackageDigest", "workflowPackageDigest")
                    ? "single-release-package-authority"
                    : null,
            "unobserved-generator-revision" =>
                !facts.TryGetProperty("observedRevisionDigest", out var observed) ||
                observed.ValueKind != JsonValueKind.String ||
                !string.Equals(
                    facts.GetProperty("declaredRevisionDigest").GetString(),
                    observed.GetString(),
                    StringComparison.Ordinal)
                    ? "generator-revision-execution-link"
                    : null,
            "caller-supplied-internal-digest" =>
                !string.Equals(
                    facts.GetProperty("digestSource").GetString(),
                    "installed-catalog",
                    StringComparison.Ordinal) ||
                ValuesDiffer(facts, "selectedDigest", "catalogDigest")
                    ? "catalog-owned-internal-digest"
                    : null,
            _ => "known-release-binding-fixture-kind",
        };
    }

    private static string? ValidateCompleteBinding(JsonElement facts)
    {
        if (facts.GetProperty("receiptContainsRandomData").GetBoolean() ||
            ValuesDiffer(facts, "firstAssemblyDigest", "secondAssemblyDigest"))
        {
            return "stable-compiler-output";
        }

        if (!facts.GetProperty("pathMapApplied").GetBoolean())
        {
            return "checkout-root-normalization";
        }

        if (ValuesDiffer(facts, "firstPackageDigest", "secondPackageDigest") ||
            ValuesDiffer(facts, "firstEntryTimestamp", "secondEntryTimestamp"))
        {
            return "package-byte-reproducibility";
        }

        if (!HasCanonicalDigest(facts, "packageSha256") ||
            !HasCanonicalDigest(facts, "assemblyDigest"))
        {
            return "canonical-selection-concreteness";
        }

        if (ValuesDiffer(facts, "manifestPackageDigest", "workflowPackageDigest"))
        {
            return "single-release-package-authority";
        }

        if (ValuesDiffer(
                facts,
                "declaredRevisionDigest",
                "observedRevisionDigest"))
        {
            return "generator-revision-execution-link";
        }

        return !string.Equals(
                facts.GetProperty("digestSource").GetString(),
                "installed-catalog",
                StringComparison.Ordinal) ||
            ValuesDiffer(facts, "selectedDigest", "catalogDigest")
                ? "catalog-owned-internal-digest"
                : null;
    }

    private static bool ValuesDiffer(
        JsonElement facts,
        string firstProperty,
        string secondProperty) =>
        !string.Equals(
            facts.GetProperty(firstProperty).GetString(),
            facts.GetProperty(secondProperty).GetString(),
            StringComparison.Ordinal);

    private static bool HasCanonicalDigest(
        JsonElement facts,
        string propertyName)
    {
        var value = facts.GetProperty(propertyName).GetString();
        return value is { Length: 71 } &&
            value.StartsWith("sha256:", StringComparison.Ordinal) &&
            value.AsSpan(7).ToString().All(static character =>
                character is >= '0' and <= '9' or >= 'a' and <= 'f');
    }
}
