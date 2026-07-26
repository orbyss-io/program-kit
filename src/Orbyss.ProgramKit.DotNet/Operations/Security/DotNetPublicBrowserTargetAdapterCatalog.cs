using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact reviewed browser-target adapters; no ambient discovery is performed.</summary>
public static class DotNetPublicBrowserTargetAdapterCatalog
{
    /// <summary>Gets the pinned .NET 10 Blazor WebAssembly OIDC adapter.</summary>
    public static DotNetPublicBrowserTargetAdapter BlazorWebAssemblyOidc { get; } =
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(
                    "pkid:adapter:program-kit:blazor-webassembly-oidc"),
                new SemanticVersion("10.0.10"),
                new Sha256Digest(
                    "sha256:b355a2bdaecbd2c03d862202e9b23a15d9ac932c1f2f43986e80f11b3ee0c093")),
            DotNetPublicBrowserTargetKind.BlazorWebAssemblyOidc,
            new ArtifactReference(
                new ProgramKitIdentifier(
                    "pkid:generator:program-kit:public-browser"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:92acc5f993c3a8da072d74229be80963ab755175aa0182be8a4da1a7d73c9248")),
            [
                new DotNetPackageReference(
                    "Microsoft.AspNetCore.Components.WebAssembly",
                    new SemanticVersion("10.0.10"),
                    new Sha256Digest(
                        "sha256:ca29a5126d5dce3bee65e62be2e0c0c390e6484758f17302a7c462f045de45a8")),
                new DotNetPackageReference(
                    "Microsoft.AspNetCore.Components.WebAssembly.Authentication",
                    new SemanticVersion("10.0.10"),
                    new Sha256Digest(
                        "sha256:ae71dd91769e5911d3eb476bee7887fbd8775a815f0fdcd5e828e47900e0780c")),
            ]);

    /// <summary>Gets the exact Playwright runtime used by generated verification.</summary>
    public static ArtifactReference Playwright { get; } =
        new(
            new ProgramKitIdentifier(
                "pkid:package:external:microsoft-playwright"),
            new SemanticVersion("1.61.0"),
            new Sha256Digest(
                "sha256:e8d2f5ce3758e640647716c25bfae8b87908aa537f204ebcfe3d14d91380817c"));
}
