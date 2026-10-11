namespace Product.Core;

/// <summary>Public identity issuer and subject form the application ownership key.</summary>
/// <param name="Issuer">Admitted public identity issuer.</param>
/// <param name="Subject">Admitted account subject.</param>
public sealed record ResourceOwner(string Issuer, string Subject);
