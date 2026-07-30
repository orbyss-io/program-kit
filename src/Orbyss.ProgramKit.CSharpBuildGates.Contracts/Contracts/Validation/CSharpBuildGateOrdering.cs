using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>
/// Owns every stable composite key used by gate definition, selection-lock,
/// scaffold, bind, and description mechanics.
/// </summary>
public static class CSharpBuildGateOrdering
{
    /// <summary>Gets the exact activation-row composite key.</summary>
    public static string ActivationKey(CSharpGateActivation value)
    {
        ArgumentNullException.ThrowIfNull(value);
        return string.Join(
            "|",
            value.ProjectProfileId.Value,
            value.SourceProfileId.Value,
            Kebab(value.Command),
            Kebab(value.Boundary),
            Kebab(value.VerificationProfile),
            string.Join(
                ",",
                value.AnalyzerComponentIds.Select(
                    static identity => identity.Value)));
    }

    /// <summary>Gets the exact expected-receipt composite key.</summary>
    public static string ExpectedReceiptKey(CSharpGateExpectedReceipt value)
    {
        ArgumentNullException.ThrowIfNull(value);
        return string.Join(
            "|",
            value.ProjectProfileId.Value,
            value.AnalyzerComponentId.Value,
            Kebab(value.VerificationProfile),
            value.ReceiptIdentity.Value);
    }

    /// <summary>Gets the exact artifact-reference composite key.</summary>
    public static string ArtifactReferenceKey(ArtifactReference value)
    {
        ArgumentNullException.ThrowIfNull(value);
        return string.Join(
            "@",
            value.Identity.Value,
            value.Version.Value,
            value.Digest.Value);
    }

    /// <summary>Gets the exact inventory-row key.</summary>
    public static string InventoryKey(CSharpGateLockedContent value)
    {
        ArgumentNullException.ThrowIfNull(value);
        return value.RepositoryRelativePath;
    }

    /// <summary>Gets the exact identifier key.</summary>
    public static string IdentityKey(ProgramKitIdentifier value) => value.Value;

    /// <summary>Projects a finite gate enum to its canonical wire token.</summary>
    public static string Kebab<TEnum>(TEnum value)
        where TEnum : struct, Enum
    {
        var source = value.ToString();
        var builder = new System.Text.StringBuilder(source.Length + 8);
        for (var index = 0; index < source.Length; index++)
        {
            if (index > 0 && char.IsUpper(source[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(source[index]));
        }

        return builder.ToString();
    }
}
