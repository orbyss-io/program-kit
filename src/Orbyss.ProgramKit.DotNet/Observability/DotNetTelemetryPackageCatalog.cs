using Orbyss.ProgramKit.DotNet.Packages;

namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Exact finite OpenTelemetry package selection for host tooling revision 1.0.0.</summary>
public static class DotNetTelemetryPackageCatalog
{
    /// <summary>The selected stable OpenTelemetry .NET release.</summary>
    public const string OpenTelemetryVersion = "1.17.0";

    /// <summary>Gets the exact direct package closure required by the base adapter.</summary>
    public static ImmutableArray<DotNetPackageReference> Packages { get; } =
    [
        Package(
            "OpenTelemetry.Exporter.OpenTelemetryProtocol",
            "564269e7c9e1826c41d0c6dcda63263adc84414e8013dd2d0e92fef401ed43d6"),
        Package(
            "OpenTelemetry.Extensions.Hosting",
            "c1eb25df47a110ef1a21fe240d1444da21e430a9efe8ec7fe0bc90766b4b0677"),
        Package(
            "OpenTelemetry.Instrumentation.AspNetCore",
            "c9d469f1ba39be71e43735141e5eb7d560306e5d9defc8d04565cb56f2ff404b"),
        Package(
            "OpenTelemetry.Instrumentation.Http",
            "40518e89567dd680e1bb77bf0bbbd45b1ab4bf97dc6a86969306f259bcc885ba"),
    ];

    private static DotNetPackageReference Package(string id, string digest) =>
        new(
            id,
            new SemanticVersion(OpenTelemetryVersion),
            new Sha256Digest(string.Concat("sha256:", digest)));
}
