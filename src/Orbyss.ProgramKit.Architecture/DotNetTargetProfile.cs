using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>
/// The minimal immutable .NET compilation target selected by a Program Kit
/// build. It deliberately contains no generator, host, or language-adapter
/// behavior. Identity and version make the selected profile self-describing;
/// when durable, they must equal the authoritative enclosing artifact metadata.
/// </summary>
public sealed record DotNetTargetProfile(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string SdkVersion,
    string RollForward,
    bool AllowPrerelease,
    string TargetFramework,
    string LanguageVersion)
{
    /// <summary>The canonical Program Kit .NET 10 target profile.</summary>
    public static DotNetTargetProfile ProgramKitDotNet10 { get; } = new(
        ProgramKitIdentifier.Parse("pkid:profile:program-kit:dotnet-10"),
        SemanticVersion.Parse("1.0.0"),
        "10.0.302",
        "disable",
        false,
        "net10.0",
        "14.0");
}
