using Microsoft.Extensions.Options;
using Nuplane.Loading;
using Nuplane.Loading.Extensions;

namespace ProgramKit.Host.Feed;

/// <summary>Preserves Nuplane validation while admitting its documented unsigned shared contracts.</summary>
internal sealed class ProgramKitLoadingOptionsValidation(LoadingOptionsValidator validator) : IValidateOptions<LoadingOptions>
{
    /// <summary>The exact unsigned host contracts required for Program Kit feature integration.</summary>
    private static readonly HashSet<string> UnsignedHostContracts =
    [
        "CShells.Abstractions",
        "CShells.AspNetCore.Abstractions",
        "ProgramKit.Tasks.Abstractions"
    ];

    /// <summary>Replaces only Nuplane's inconsistent token-format adapter, retaining all other validators.</summary>
    public static void ReplaceNuplaneAdapter(IServiceCollection services)
    {
        for (var index = services.Count - 1; index >= 0; index--)
        {
            var descriptor = services[index];
            if (descriptor.ServiceType == typeof(IValidateOptions<LoadingOptions>)
                && descriptor.ImplementationType == typeof(LoadingOptionsValidation))
                services.RemoveAt(index);
        }
        services.AddSingleton<IValidateOptions<LoadingOptions>, ProgramKitLoadingOptionsValidation>();
    }

    /// <inheritdoc />
    public ValidateOptionsResult Validate(string? name, LoadingOptions options)
    {
        var permittedErrors = options.SharedAssemblies
            .Where(identity =>
                UnsignedHostContracts.Contains(identity.Name)
                && string.IsNullOrEmpty(identity.PublicKeyToken)
                && identity.MajorVersion == 0)
            .Select(identity => $"Shared assembly '{identity.Name}' must have a 16-char hex public key token.")
            .ToHashSet(StringComparer.Ordinal);
        var errors = validator.Validate(options)
            .Where(error => !permittedErrors.Contains(error))
            .ToArray();
        return errors.Length == 0 ? ValidateOptionsResult.Success : ValidateOptionsResult.Fail(errors);
    }
}
