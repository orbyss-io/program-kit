namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Exact reviewed Kiota C# tool and package selection.</summary>
internal static class KiotaToolSelection
{
    internal const string ToolVersion = "1.34.1";

    internal const string ToolVersionEvidence =
        "1.34.1+9f9cfb3b1cb9b5311a214ea6ce0f69943c523005";

    internal const string ManifestDigest =
        "sha256:020e555dabebddca1ec6380f48ec042a38e8f5db45e820e58936c4a8842c8f1c";

    internal const string PackageDigest =
        "sha256:4aa14f12d573d5644eb167b837c4fa10d7d7b7ec4a6634b8bc4026269f9a7671";

    internal const string EntryRelativePath = "tools/net10.0/any/kiota.dll";

    internal const string EntryDigest =
        "sha256:c123ecc6cbff7d65699b4ad79c87857a5b95f48bfe2364a64a5c792d212a5b6f";

    internal const string SourceCommit =
        "9f9cfb3b1cb9b5311a214ea6ce0f69943c523005";
}
