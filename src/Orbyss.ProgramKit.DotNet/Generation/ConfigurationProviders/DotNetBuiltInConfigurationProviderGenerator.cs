using System.Text;
using Orbyss.ProgramKit.DotNet.Configuration;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>Renders one reviewed built-in provider descriptor.</summary>
internal sealed class DotNetBuiltInConfigurationProviderGenerator(
    DotNetConfigurationProviderDescriptor descriptor) :
    IDotNetConfigurationProviderGenerator
{
    /// <inheritdoc />
    public DotNetConfigurationProviderDescriptor Descriptor { get; } =
        descriptor;

    /// <inheritdoc />
    public string RenderRegistration(DotNetConfigurationSource source)
    {
        ArgumentNullException.ThrowIfNull(source);
        var builder = new StringBuilder();
        switch (Descriptor.Kind)
        {
            case DotNetConfigurationProviderKind.JsonFile:
                builder
                    .Append("builder.Configuration.AddJsonFile(")
                    .Append(DotNetSourceText.CSharpLiteral(source.Path!))
                    .Append(", optional: ")
                    .Append(source.Optional ? "true" : "false")
                    .Append(", reloadOnChange: ")
                    .Append(source.Reload.Enabled ? "true" : "false")
                    .AppendLine(");");
                break;
            case DotNetConfigurationProviderKind.EnvironmentVariables:
                builder
                    .Append("builder.Configuration.AddEnvironmentVariables(")
                    .Append(source.Prefix is null
                        ? string.Empty
                        : DotNetSourceText.CSharpLiteral(source.Prefix))
                    .AppendLine(");");
                break;
            case DotNetConfigurationProviderKind.CommandLine:
                builder.AppendLine("builder.Configuration.AddCommandLine(args);");
                break;
            case DotNetConfigurationProviderKind.InMemory:
                RenderMemory(builder, "builder.Configuration", source);
                break;
            case DotNetConfigurationProviderKind.UserSecrets:
                builder.AppendLine("if (builder.Environment.IsDevelopment())");
                builder.AppendLine("{");
                builder
                    .Append("    builder.Configuration.AddUserSecrets(")
                    .Append(DotNetSourceText.CSharpLiteral(source.UserSecretsId!))
                    .Append(", reloadOnChange: ")
                    .Append(source.Reload.Enabled ? "true" : "false")
                    .AppendLine(");");
                builder.AppendLine("}");
                break;
            case DotNetConfigurationProviderKind.KeyPerFile:
                builder
                    .Append("builder.Configuration.AddKeyPerFile(")
                    .Append(DotNetSourceText.CSharpLiteral(source.Path!))
                    .Append(", optional: ")
                    .Append(source.Optional ? "true" : "false")
                    .Append(", reloadOnChange: ")
                    .Append(source.Reload.Enabled ? "true" : "false")
                    .AppendLine(");");
                break;
            case DotNetConfigurationProviderKind.ChainedConfiguration:
                var variable = string.Concat(
                    "programKitChainedConfiguration",
                    source.Order.ToString(
                        System.Globalization.CultureInfo.InvariantCulture));
                builder
                    .Append("var ")
                    .Append(variable)
                    .AppendLine(" = new ConfigurationBuilder();");
                RenderMemory(builder, variable, source);
                builder
                    .Append("builder.Configuration.AddConfiguration(")
                    .Append(variable)
                    .AppendLine(".Build(), shouldDisposeConfiguration: true);");
                break;
            default:
                throw new NotSupportedException(
                    "PKNET008 The exact configuration provider generator is not registered.");
        }

        return builder.ToString();
    }

    private static void RenderMemory(
        StringBuilder builder,
        string target,
        DotNetConfigurationSource source)
    {
        builder
            .Append(target)
            .AppendLine(".AddInMemoryCollection(");
        builder.AppendLine(
            "    new Dictionary<string, string?>(StringComparer.Ordinal)");
        builder.AppendLine("    {");
        foreach (var value in source.InitialValues.OrderBy(
                     static value => value.Key,
                     StringComparer.Ordinal))
        {
            builder
                .Append("        [")
                .Append(DotNetSourceText.CSharpLiteral(value.Key))
                .Append("] = ")
                .Append(DotNetSourceText.CSharpLiteral(value.Value))
                .AppendLine(",");
        }

        builder.AppendLine("    });");
    }
}
