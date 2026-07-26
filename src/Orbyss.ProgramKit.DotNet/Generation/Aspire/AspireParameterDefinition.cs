namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>
/// One configuration-backed AppHost parameter. Secret references are identities,
/// never secret values.
/// </summary>
public sealed record AspireParameterDefinition(
    string Name,
    string ConfigurationKey,
    SecretResolution.Contracts.SecretReferenceDescriptor? SecretReference);
