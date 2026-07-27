using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Operations.FastEndpoints;

/// <summary>Reviewed exact FastEndpoints and CShells adapter selection.</summary>
public static class DotNetFastEndpointsSelection
{
    /// <summary>Gets the exact provider-profile revision.</summary>
    public static ArtifactReference ProfileRevision { get; } =
        new(
            new ProgramKitIdentifier(
                "pkid:profile:program-kit:dotnet-fastendpoints"),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                "sha256:c6fef42c36215e83c9d9d63259e132bbb3fc0d7ff543c6a9694bc18b4064c854"));

    /// <summary>Gets the exact CShells integration package.</summary>
    public static DotNetPackageReference ShellAdapterPackage { get; } =
        new(
            "CShells.FastEndpoints",
            new SemanticVersion("0.0.28"),
            new Sha256Digest(
                "sha256:4db7532f26b3248a126427bd0faa112b91ceccb1eccd667bb13630060536a4c7"));

    /// <summary>Gets the exact compatible FastEndpoints runtime package.</summary>
    public static DotNetPackageReference FastEndpointsPackage { get; } =
        new(
            "FastEndpoints",
            new SemanticVersion("7.2.0"),
            new Sha256Digest(
                "sha256:f0e85972e8fb685fc178bfa49dafec85d81fb32d4282e643517150ac948ce61e"));

    /// <summary>Creates the complete reviewed configuration.</summary>
    public static DotNetFastEndpointsConfiguration Create() =>
        new(
            ProfileRevision,
            ShellAdapterPackage,
            FastEndpointsPackage);
}
