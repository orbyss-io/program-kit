namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Reviewed package closure for one selectable Aspire integration.</summary>
public sealed record AspireIntegrationDescriptor(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string PackageName,
    SemanticVersion PackageVersion,
    Sha256Digest PackageSha256);
