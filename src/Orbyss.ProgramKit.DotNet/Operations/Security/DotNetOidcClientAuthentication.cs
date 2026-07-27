using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Non-secret reference and runtime binding for confidential client authentication.</summary>
public sealed record DotNetOidcClientAuthentication(
    [property: JsonPropertyName("method")] DotNetOidcClientAuthenticationMethod Method,
    [property: JsonPropertyName("reference")] SecretReferenceDescriptor Reference,
    [property: JsonPropertyName("configurationKey")] string? ConfigurationKey);
