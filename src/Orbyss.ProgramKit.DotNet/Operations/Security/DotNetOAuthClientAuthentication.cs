using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Non-secret reference used to authenticate one OAuth service client.</summary>
public sealed record DotNetOAuthClientAuthentication(
    [property: JsonPropertyName("method")] DotNetOAuthClientAuthenticationMethod Method,
    [property: JsonPropertyName("reference")] SecretReferenceDescriptor Reference,
    [property: JsonPropertyName("configurationKey")] string? ConfigurationKey);
