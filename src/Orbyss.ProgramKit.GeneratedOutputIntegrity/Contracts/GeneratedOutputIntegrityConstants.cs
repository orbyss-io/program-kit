namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Frozen identifiers and paths for generated-output integrity revision 1.0.0.</summary>
public static class GeneratedOutputIntegrityConstants
{
    /// <summary>Canonical manifest schema identity.</summary>
    public const string ManifestSchema =
        "pkid:schema:program-kit:generated-output-manifest@1.0.0";

    /// <summary>Exact canonical manifest schema bytes.</summary>
    public const string ManifestSchemaSha256 =
        "sha256:4b7a636fd8ca7176736172a831d75dddc18b7239185d97193b1c2ebb219f2faf";

    /// <summary>Canonical external-anchor schema identity.</summary>
    public const string AnchorSchema =
        "pkid:schema:program-kit:generated-output-anchor@1.0.0";

    /// <summary>Exact canonical external-anchor schema bytes.</summary>
    public const string AnchorSchemaSha256 =
        "sha256:445ddd9e8b0fff492c3ade146d4d2ed9979e4d421f83429ee731fa73ce4406e1";

    /// <summary>Frozen integrity format revision.</summary>
    public const string FormatVersion = "1.0.0";

    /// <summary>Ownership classification for a complete generated host root.</summary>
    public const string Ownership = "program-kit-generated-host";

    /// <summary>Normalized in-root manifest path.</summary>
    public const string ManifestRelativePath =
        ".program-kit/generated-output.manifest.json";

    /// <summary>Suffix used for the sibling external anchor.</summary>
    public const string AnchorSuffix =
        ".program-kit-generated-output.anchor.json";

    /// <summary>Suffix used for a recoverable sibling publication transaction.</summary>
    public const string TransactionSuffix =
        ".program-kit-generated-output.transaction";
}
