using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Configuration.Azure;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>
/// Deterministic Azure provider adapter. It emits endpoint and reference
/// identity only; a consumer-authored partial method supplies TokenCredential.
/// </summary>
public sealed class DotNetAzureConfigurationProviderGenerator :
    IDotNetConfigurationProviderGenerator
{
    /// <summary>Initializes a generator for one exact Azure descriptor.</summary>
    public DotNetAzureConfigurationProviderGenerator(
        DotNetConfigurationProviderDescriptor descriptor)
    {
        if (!DotNetAzureConfigurationProviderCatalog.Descriptors.Contains(descriptor))
        {
            throw new ArgumentException(
                "The generator requires one exact reviewed Azure configuration descriptor.",
                nameof(descriptor));
        }

        Descriptor = descriptor;
    }

    /// <inheritdoc />
    public DotNetConfigurationProviderDescriptor Descriptor { get; }

    /// <inheritdoc />
    public string RenderRegistration(DotNetConfigurationSource source) =>
        throw new NotSupportedException(
            "PKNET024 Azure configuration generation requires exact host adapter composition.");

    /// <inheritdoc />
    public string RenderRegistration(
        DotNetConfigurationSource source,
        DotNetHostDefinition host)
    {
        var binding = Resolve(source, host);
        var suffix = Suffix(source.Identity.Value);
        var builder = new StringBuilder();
        RenderCredentialResolution(
            builder,
            binding.CredentialResolution,
            binding.CredentialResolutionTimeoutSeconds,
            string.Concat("azureCredential", suffix),
            string.Concat("ResolveProgramKitAzureCredential", suffix, "Async"),
            string.Concat("azureCredentialTimeout", suffix));

        if (binding.ProviderKind != DotNetAzureConfigurationProviderKind.KeyVault)
        {
            throw new NotSupportedException(
                "PKNET024 The Azure configuration provider kind is unsupported.");
        }

        RenderKeyVault(builder, binding, suffix);
        return builder.ToString();
    }

    /// <inheritdoc />
    public ImmutableArray<GeneratedOutput> Compile(
        DotNetConfigurationSource source,
        DotNetHostDefinition host)
    {
        var binding = Resolve(source, host);
        var suffix = Suffix(source.Identity.Value);
        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        outputs.Add(new GeneratedOutput(
            string.Concat(
                "ProgramKitGenerated/Configuration/AzureCredentialBinding",
                suffix,
                ".cs"),
            DotNetSourceText.Utf8(RenderCredentialContract(binding, suffix))));
        outputs.Add(new GeneratedOutput(
            string.Concat(
                "ProgramKitGenerated/Configuration/IActiveKeyVaultSecretPolicy",
                suffix,
                ".cs"),
            DotNetSourceText.Utf8(RenderActiveSecretPolicy(suffix))));
        outputs.Add(new GeneratedOutput(
            string.Concat(
                "ProgramKitGenerated/Configuration/ActiveKeyVaultSecretManager",
                suffix,
                ".cs"),
            DotNetSourceText.Utf8(RenderActiveSecretManager(suffix))));

        outputs.Add(new GeneratedOutput(
            string.Concat("configuration/azure/", suffix, ".json"),
            DotNetSourceText.Utf8(RenderEvidence(source, binding))));
        return outputs.ToImmutable();
    }

    private DotNetAzureConfigurationBinding Resolve(
        DotNetConfigurationSource source,
        DotNetHostDefinition host)
    {
        if (source.ProviderRevision != Descriptor.ProviderRevision ||
            source.ProviderKind != DotNetConfigurationProviderKind.RegisteredAdapter ||
            host.AzureConfiguration is null)
        {
            throw new NotSupportedException(
                "PKNET024 The exact Azure source, descriptor, and composition are not bound.");
        }

        var binding = host.AzureConfiguration.Bindings.SingleOrDefault(
            candidate => candidate.SourceIdentity == source.Identity) ??
            throw new NotSupportedException(
                "PKNET024 The Azure source has no exact adapter binding.");
        if (Descriptor != DotNetAzureConfigurationProviderCatalog.KeyVault ||
            binding.ProviderKind != DotNetAzureConfigurationProviderKind.KeyVault)
        {
            throw new NotSupportedException(
                "PKNET024 The Azure adapter kind does not match the exact provider revision.");
        }

        return binding;
    }

    private static void RenderCredentialResolution(
        StringBuilder builder,
        SecretResolutionContract contract,
        int timeoutSeconds,
        string variable,
        string method,
        string timeoutVariable)
    {
        builder
            .Append("using var ")
            .Append(timeoutVariable)
            .Append(" = new global::System.Threading.CancellationTokenSource(global::System.TimeSpan.FromSeconds(")
            .Append(timeoutSeconds.ToString(CultureInfo.InvariantCulture))
            .AppendLine("));");
        builder
            .Append("var ")
            .Append(variable)
            .Append(" = await ")
            .Append(method)
            .Append('(')
            .Append(DotNetSourceText.CSharpLiteral(contract.Reference.Identity.Value))
            .Append(", ")
            .Append(timeoutVariable)
            .AppendLine(".Token);");
    }

    private static void RenderKeyVault(
        StringBuilder builder,
        DotNetAzureConfigurationBinding binding,
        string suffix)
    {
        var options = binding.KeyVault!;
        builder.AppendLine(
            "global::Azure.Extensions.AspNetCore.Configuration.Secrets.AzureKeyVaultConfigurationExtensions.AddAzureKeyVault(");
        builder.AppendLine("    builder.Configuration,");
        builder
            .Append("    new global::System.Uri(")
            .Append(DotNetSourceText.CSharpLiteral(binding.Endpoint.AbsoluteUri))
            .AppendLine("),");
        builder.Append("    azureCredential").Append(suffix).AppendLine(",");
        builder.AppendLine(
            "    new global::Azure.Extensions.AspNetCore.Configuration.Secrets.AzureKeyVaultConfigurationOptions");
        builder.AppendLine("    {");
        builder
            .Append("        Manager = new global::GeneratedHost.Configuration.ActiveKeyVaultSecretManager")
            .Append(suffix)
            .AppendLine("(),");
        builder.Append("        ReloadInterval = ");
        if (options.ReloadIntervalSeconds is { } interval)
        {
            builder
                .Append("global::System.TimeSpan.FromSeconds(")
                .Append(interval.ToString(CultureInfo.InvariantCulture))
                .AppendLine("),");
        }
        else
        {
            builder.AppendLine("null,");
        }

        builder.AppendLine("    });");
    }

    private static string RenderCredentialContract(
        DotNetAzureConfigurationBinding _,
        string suffix)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine();
        builder.AppendLine("namespace GeneratedHost.Composition;");
        builder.AppendLine();
        builder.AppendLine("internal static partial class Program");
        builder.AppendLine("{");
        builder
            .Append("    private static partial global::System.Threading.Tasks.ValueTask<global::Azure.Core.TokenCredential> ResolveProgramKitAzureCredential")
            .Append(suffix)
            .AppendLine("Async(");
        builder.AppendLine("        string referenceIdentity,");
        builder.AppendLine("        global::System.Threading.CancellationToken cancellationToken);");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderActiveSecretPolicy(string suffix) =>
        string.Concat(
            "// <auto-generated program-kit>\n",
            "#nullable enable\n\n",
            "namespace GeneratedHost.Configuration;\n\n",
            "internal interface IActiveKeyVaultSecretPolicy", suffix, "\n",
            "{\n",
            "    string GetKey(global::Azure.Security.KeyVault.Secrets.KeyVaultSecret secret);\n",
            "    global::System.Collections.Generic.Dictionary<string, string?> GetData(global::System.Collections.Generic.IEnumerable<global::Azure.Security.KeyVault.Secrets.KeyVaultSecret> secrets);\n",
            "    bool Load(global::Azure.Security.KeyVault.Secrets.SecretProperties secret);\n",
            "}\n");

    private static string RenderActiveSecretManager(string suffix) =>
        string.Concat(
            "// <auto-generated program-kit>\n",
            "#nullable enable\n\n",
            "namespace GeneratedHost.Configuration;\n\n",
            "internal sealed class ActiveKeyVaultSecretManager", suffix,
            " : global::Azure.Extensions.AspNetCore.Configuration.Secrets.KeyVaultSecretManager,\n",
            "   IActiveKeyVaultSecretPolicy", suffix, "\n",
            "{\n",
            "    public override bool Load(global::Azure.Security.KeyVault.Secrets.SecretProperties secret)\n",
            "    {\n",
            "        var now = global::System.DateTimeOffset.UtcNow;\n",
            "        return secret.Enabled is not false &&\n",
            "               (secret.NotBefore is null || secret.NotBefore <= now) &&\n",
            "               (secret.ExpiresOn is null || secret.ExpiresOn > now);\n",
            "    }\n",
            "}\n");

    private static string RenderEvidence(
        DotNetConfigurationSource source,
        DotNetAzureConfigurationBinding binding)
    {
        var endpointDigest = Convert.ToHexStringLower(
            SHA256.HashData(Encoding.UTF8.GetBytes(binding.Endpoint.AbsoluteUri)));
        return string.Concat(
            "{\n",
            "  \"source\": ", DotNetSourceText.JsonLiteral(source.Identity.Value), ",\n",
            "  \"providerKind\": ", DotNetSourceText.JsonLiteral(EnumText(binding.ProviderKind)), ",\n",
            "  \"endpointSha256\": \"sha256:", endpointDigest, "\",\n",
            "  \"credentialResultKind\": ",
            DotNetSourceText.JsonLiteral(EnumText(binding.CredentialResolution.Reference.ExpectedResultKind)), ",\n",
            "  \"credentialReaction\": ",
            DotNetSourceText.JsonLiteral(EnumText(binding.CredentialResolution.Consumption.Reaction)), ",\n",
            "  \"locatorClassification\": ",
            DotNetSourceText.JsonLiteral(EnumText(binding.CredentialResolution.Reference.LocatorClassification)), ",\n",
            "  \"operationalMetadataRedacted\": true,\n",
            "  \"outageBehavior\": \"startup-or-poll-failure-is-provider-specific\"\n",
            "}\n");
    }

    private static string Suffix(string identity) =>
        Convert.ToHexStringLower(
            SHA256.HashData(Encoding.UTF8.GetBytes(identity)))[..12];

    private static string EnumText<T>(T value)
        where T : struct, Enum
    {
        var source = value.ToString();
        var builder = new StringBuilder();
        for (var index = 0; index < source.Length; index++)
        {
            var character = source[index];
            if (index > 0 && char.IsUpper(character))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(character));
        }

        return builder.ToString();
    }
}
