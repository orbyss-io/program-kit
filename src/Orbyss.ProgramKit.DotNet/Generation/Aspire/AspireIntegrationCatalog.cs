namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Exact finite Aspire integration catalog for AppHost generation.</summary>
public static class AspireIntegrationCatalog
{
    /// <summary>The required core AppHost integration.</summary>
    public static AspireIntegrationDescriptor AppHost { get; } = new(
        new ProgramKitIdentifier("pkid:integration:program-kit:aspire-apphost"),
        new SemanticVersion("1.0.0"),
        "Aspire.Hosting.AppHost",
        new SemanticVersion("13.4.6"),
        new Sha256Digest(
            "sha256:f387c6ec2839ff25cc7da9b14278d8e24eaada2843579751cafd1a59f18f6a55"));

    /// <summary>Gets all exact currently registered integrations.</summary>
    public static ImmutableArray<AspireIntegrationDescriptor> Descriptors { get; } =
        [AppHost];
}
