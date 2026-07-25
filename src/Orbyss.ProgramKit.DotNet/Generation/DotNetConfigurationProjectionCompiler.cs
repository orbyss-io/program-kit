using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Deterministic configuration-definition compiler for the supported .NET target.</summary>
public sealed class DotNetConfigurationProjectionCompiler :
    IDotNetConfigurationProjectionCompiler
{
    /// <inheritdoc />
    public ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        var orderedBindings = host.ConfigurationBindings
            .OrderBy(
                static item => item.Definition.Identity.Value,
                StringComparer.Ordinal)
            .ThenBy(static item => item.OptionsName, StringComparer.Ordinal)
            .ToArray();
        foreach (var binding in orderedBindings.DistinctBy(static item =>
                     string.Concat(
                         item.Definition.Identity.Value,
                         "@",
                         item.Definition.Version.Value)))
        {
            var definition = binding.Definition;
            outputs.Add(Output(
                string.Concat(
                    "ProgramKitGenerated/Configuration/",
                    definition.TypeName,
                    ".cs"),
                RenderOptions(definition)));
            outputs.Add(Output(
                string.Concat(
                    "ProgramKitGenerated/Configuration/",
                    definition.TypeName,
                    "Validator.cs"),
                RenderOptionsValidator(definition)));
        }

        foreach (var binding in orderedBindings.Where(static binding =>
                     binding.ChangeReaction !=
                     DotNetConfigurationChangeReaction.None))
        {
            var subscriptionName = MonitorSubscriptionName(binding);
            outputs.Add(Output(
                string.Concat(
                    "ProgramKitGenerated/Configuration/",
                    subscriptionName,
                    ".cs"),
                RenderMonitorSubscription(binding, subscriptionName)));
        }
        foreach (var definition in orderedBindings
                     .Where(static binding =>
                         binding.ChangeReaction ==
                         DotNetConfigurationChangeReaction.ConsumerOwnedQueue)
                     .Select(static binding => binding.Definition)
                     .DistinctBy(static definition => string.Concat(
                         definition.Identity.Value,
                         "@",
                         definition.Version.Value)))
        {
            outputs.Add(Output(
                string.Concat(
                    "ProgramKitGenerated/Configuration/I",
                    definition.TypeName,
                    "ChangeConsumer.cs"),
                RenderChangeConsumer(definition)));
        }

        outputs.Add(Output(
            "configuration/generated/appsettings.generated.json",
            RenderConfiguration(host.ConfigurationBindings, false)));
        foreach (var source in host.ConfigurationSources.Where(static source =>
                     source.ProviderKind ==
                     DotNetConfigurationProviderKind.JsonFile))
        {
            var bindings = host.ConfigurationBindings
                .Where(binding =>
                    binding.SourceIdentities.Contains(source.Identity))
                .ToImmutableArray();
            outputs.Add(Output(
                source.Path!,
                RenderConfiguration(bindings, false)));
        }
        outputs.Add(Output(
            "configuration/examples/appsettings.example.json",
            RenderConfiguration(host.ConfigurationBindings, true)));
        outputs.Add(Output(
            "configuration/developer/appsettings.Development.json",
            RenderDeveloperOverlay(host.ConfigurationBindings)));
        outputs.Add(Output(
            "configuration/environment-map.json",
            RenderEnvironmentMap(host.ConfigurationBindings)));
        outputs.Add(Output(
            "configuration/key-per-file-map.json",
            RenderKeyPerFileMap(host.ConfigurationBindings)));
        outputs.Add(Output(
            "configuration/provider-bindings.json",
            RenderProviderBindings(host.ConfigurationSources)));
        outputs.Add(Output(
            "configuration/validation-report.json",
            RenderValidationReport(host.ConfigurationBindings)));
        outputs.Add(Output(
            "configuration/provenance.json",
            RenderProvenance(host)));
        outputs.Add(Output(
            "configuration/ownership.json",
            RenderOwnership(host.ConfigurationSources)));
        return outputs.ToImmutable();
    }

    /// <inheritdoc />
    public string RenderRegistration(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        var builder = new StringBuilder();
        var orderedBindings = host.ConfigurationBindings
            .OrderBy(
                static item => item.Definition.Identity.Value,
                StringComparer.Ordinal)
            .ThenBy(static item => item.OptionsName, StringComparer.Ordinal)
            .ToArray();
        if (!host.ConfigurationSources.IsDefaultOrEmpty)
        {
            builder.AppendLine("builder.Configuration.Sources.Clear();");
        }

        foreach (var source in host.ConfigurationSources)
        {
            RenderProviderRegistration(builder, source);
        }

        foreach (var definition in orderedBindings
                     .Select(static binding => binding.Definition)
                     .DistinctBy(static definition => string.Concat(
                         definition.Identity.Value,
                         "@",
                         definition.Version.Value)))
        {
            var typeName = string.Concat(
                "global::",
                definition.Namespace,
                ".",
                definition.TypeName);
            builder
                .Append("builder.Services.AddSingleton<global::Microsoft.Extensions.Options.IValidateOptions<")
                .Append(typeName)
                .Append(">, global::")
                .Append(definition.Namespace)
                .Append('.')
                .Append(definition.TypeName)
                .AppendLine("Validator>();");
        }

        foreach (var binding in orderedBindings)
        {
            var typeName = string.Concat(
                "global::",
                binding.Definition.Namespace,
                ".",
                binding.Definition.TypeName);
            builder
                .Append("builder.Services.AddOptions<")
                .Append(typeName)
                .Append(">(")
                .Append(string.IsNullOrEmpty(binding.OptionsName)
                    ? "global::Microsoft.Extensions.Options.Options.DefaultName"
                    : DotNetSourceText.CSharpLiteral(binding.OptionsName))
                .AppendLine(")");
            builder
                .Append("    .Bind(builder.Configuration.GetRequiredSection(")
                .Append(DotNetSourceText.CSharpLiteral(binding.Definition.Section))
                .AppendLine("))");
            if (binding.ValidateOnStart)
            {
                builder.AppendLine("    .ValidateOnStart();");
            }
            else
            {
                builder.AppendLine("    ;");
            }

            if (binding.ChangeReaction != DotNetConfigurationChangeReaction.None)
            {
                var subscription = string.Concat(
                    "global::",
                    binding.Definition.Namespace,
                    ".",
                    MonitorSubscriptionName(binding));
                builder
                    .Append("builder.Services.AddSingleton<")
                    .Append(subscription)
                    .AppendLine(">();");
                builder
                    .Append("builder.Services.AddHostedService(serviceProvider => serviceProvider.GetRequiredService<")
                    .Append(subscription)
                    .AppendLine(">());");
            }
        }

        return builder.ToString();
    }

    private static void RenderProviderRegistration(
        StringBuilder builder,
        DotNetConfigurationSource source)
    {
        if (source.Reload.Capability == DotNetConfigurationReloadCapability.ExplicitRefresh)
        {
            throw new NotSupportedException(
                "PKNET007 Explicit-refresh providers require a later approved provider adapter.");
        }

        switch (source.ProviderKind)
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
            case DotNetConfigurationProviderKind.KeyPerFile:
                builder
                    .Append("builder.Configuration.AddKeyPerFile(")
                    .Append(DotNetSourceText.CSharpLiteral(source.Path!))
                    .Append(", optional: ")
                    .Append(source.Optional ? "true" : "false")
                    .AppendLine(");");
                break;
            default:
                throw new NotSupportedException(
                    "PKNET007 The requested configuration provider target is unsupported.");
        }
    }

    private static string RenderOptions(DotNetConfigurationDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine("using System.ComponentModel.DataAnnotations;");
        builder.AppendLine();
        builder.Append("namespace ").Append(definition.Namespace).AppendLine(";");
        builder.AppendLine();
        builder
            .Append("/// <summary>Typed Options generated from ")
            .Append(definition.Identity.Value)
            .AppendLine(".</summary>");
        builder
            .Append("public sealed class ")
            .Append(definition.TypeName)
            .AppendLine();
        builder.AppendLine("{");
        foreach (var property in definition.Properties)
        {
            RenderValidationAttributes(builder, property);
            builder
                .Append("    /// <summary>Value bound from configuration key ")
                .Append(property.Key)
                .AppendLine(".</summary>");
            builder
                .Append("    public ")
                .Append(PropertyType(property))
                .Append(' ')
                .Append(property.PropertyName)
                .Append(" { get; set; }");
            if (property.DefaultValue is not null)
            {
                builder
                    .Append(" = ")
                    .Append(CSharpValue(property.ValueKind, property.DefaultValue))
                    .Append(';');
            }

            builder.AppendLine();
            builder.AppendLine();
        }

        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderOptionsValidator(
        DotNetConfigurationDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine("using Microsoft.Extensions.Options;");
        builder.AppendLine();
        builder.Append("namespace ").Append(definition.Namespace).AppendLine(";");
        builder.AppendLine();
        builder.AppendLine("/// <summary>Source-generated structural Options validator.</summary>");
        builder.AppendLine("[OptionsValidator]");
        builder
            .Append("public sealed partial class ")
            .Append(definition.TypeName)
            .Append("Validator : IValidateOptions<")
            .Append(definition.TypeName)
            .AppendLine(">");
        builder.AppendLine("{");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static void RenderValidationAttributes(
        StringBuilder builder,
        DotNetConfigurationProperty property)
    {
        if (property.Required)
        {
            builder.AppendLine("    [Required]");
        }

        var validation = property.Validation;
        if (validation.MaximumLength is not null)
        {
            builder
                .Append("    [StringLength(")
                .Append(validation.MaximumLength.Value.ToString(CultureInfo.InvariantCulture));
            if (validation.MinimumLength is not null)
            {
                builder
                    .Append(", MinimumLength = ")
                    .Append(validation.MinimumLength.Value.ToString(CultureInfo.InvariantCulture));
            }

            builder.AppendLine(")]");
        }
        else if (validation.MinimumLength is not null)
        {
            builder
                .Append("    [MinLength(")
                .Append(validation.MinimumLength.Value.ToString(CultureInfo.InvariantCulture))
                .AppendLine(")]");
        }

        if (validation.RegularExpression is not null)
        {
            builder
                .Append("    [RegularExpression(")
                .Append(DotNetSourceText.CSharpLiteral(validation.RegularExpression))
                .AppendLine(")]");
        }

        if (validation.MinimumValue is not null &&
            validation.MaximumValue is not null)
        {
            builder
                .Append("    [Range(typeof(")
                .Append(NonNullableType(property.ValueKind))
                .Append("), ")
                .Append(DotNetSourceText.CSharpLiteral(validation.MinimumValue))
                .Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(validation.MaximumValue))
                .AppendLine(")]");
        }
    }

    private static string PropertyType(DotNetConfigurationProperty property) =>
        string.Concat(
            NonNullableType(property.ValueKind),
            property.Required && property.DefaultValue is not null ? string.Empty : "?");

    private static string NonNullableType(DotNetConfigurationValueKind kind) =>
        kind switch
        {
            DotNetConfigurationValueKind.Text => "string",
            DotNetConfigurationValueKind.Boolean => "bool",
            DotNetConfigurationValueKind.WholeNumber32 => "int",
            DotNetConfigurationValueKind.WholeNumber64 => "long",
            DotNetConfigurationValueKind.DecimalNumber => "decimal",
            DotNetConfigurationValueKind.FloatingPoint => "double",
            DotNetConfigurationValueKind.AbsoluteUri => "global::System.Uri",
            DotNetConfigurationValueKind.Duration => "global::System.TimeSpan",
            _ => throw new NotSupportedException(
                "PKNET007 The configuration scalar target is unsupported."),
        };

    private static string CSharpValue(
        DotNetConfigurationValueKind kind,
        string value) =>
        kind switch
        {
            DotNetConfigurationValueKind.Text => DotNetSourceText.CSharpLiteral(value),
            DotNetConfigurationValueKind.Boolean => value.ToLowerInvariant(),
            DotNetConfigurationValueKind.WholeNumber32 => value,
            DotNetConfigurationValueKind.WholeNumber64 => string.Concat(value, "L"),
            DotNetConfigurationValueKind.DecimalNumber => string.Concat(value, "M"),
            DotNetConfigurationValueKind.FloatingPoint => string.Concat(value, "D"),
            DotNetConfigurationValueKind.AbsoluteUri => string.Concat(
                "new global::System.Uri(",
                DotNetSourceText.CSharpLiteral(value),
                ", global::System.UriKind.Absolute)"),
            DotNetConfigurationValueKind.Duration => string.Concat(
                "global::System.TimeSpan.Parse(",
                DotNetSourceText.CSharpLiteral(value),
                ", global::System.Globalization.CultureInfo.InvariantCulture)"),
            _ => throw new NotSupportedException(
                "PKNET007 The configuration scalar target is unsupported."),
        };

    private static string RenderMonitorSubscription(
        DotNetConfigurationBinding binding,
        string subscriptionName)
    {
        if (binding.ChangeReaction ==
            DotNetConfigurationChangeReaction.ConsumerOwnedQueue)
        {
            return RenderQueuedMonitorSubscription(
                binding,
                subscriptionName);
        }

        var definition = binding.Definition;
        var typeName = definition.TypeName;
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine("using Microsoft.Extensions.Hosting;");
        builder.AppendLine("using Microsoft.Extensions.Logging;");
        builder.AppendLine("using Microsoft.Extensions.Options;");
        builder.AppendLine();
        builder.Append("namespace ").Append(definition.Namespace).AppendLine(";");
        builder.AppendLine();
        builder.AppendLine("/// <summary>Owns one bounded and redacted monitored Options subscription.</summary>");
        builder
            .Append("public sealed class ")
            .Append(subscriptionName)
            .AppendLine(" : IHostedService, IDisposable");
        builder.AppendLine("{");
        builder
            .Append("    private readonly IOptionsMonitor<")
            .Append(typeName)
            .AppendLine("> monitor;");
        builder
            .Append("    private readonly ILogger<")
            .Append(typeName)
            .AppendLine("> logger;");
        builder.AppendLine("    private IDisposable? subscription;");
        builder.AppendLine();
        builder.AppendLine("    /// <summary>Initializes the bounded subscription with framework-owned dependencies.</summary>");
        builder
            .Append("    public ")
            .Append(subscriptionName)
            .Append("(IOptionsMonitor<")
            .Append(typeName)
            .Append("> monitor, ILogger<")
            .Append(typeName)
            .AppendLine("> logger)");
        builder.AppendLine("    {");
        builder.AppendLine("        this.monitor = monitor;");
        builder.AppendLine("        this.logger = logger;");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    public Task StartAsync(CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        cancellationToken.ThrowIfCancellationRequested();");
        builder.AppendLine("        subscription = monitor.OnChange((_, optionsName) =>");
        builder.AppendLine("        {");
        builder.AppendLine("            var normalizedOptionsName = optionsName ?? Options.DefaultName;");
        builder
            .Append("            if (!string.Equals(normalizedOptionsName, ")
            .Append(DotNetSourceText.CSharpLiteral(binding.OptionsName))
            .AppendLine(", StringComparison.Ordinal))");
        builder.AppendLine("            {");
        builder.AppendLine("                return;");
        builder.AppendLine("            }");
        builder
            .Append("            logger.LogInformation(")
            .Append(DotNetSourceText.CSharpLiteral(
                "Validated configuration change observed for {DefinitionIdentity} and Options name {OptionsName}; values and references are redacted."))
            .Append(", ")
            .Append(DotNetSourceText.CSharpLiteral(definition.Identity.Value))
            .AppendLine(", normalizedOptionsName);");
        builder.AppendLine("        });");
        builder.AppendLine("        return Task.CompletedTask;");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    public Task StopAsync(CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        _ = cancellationToken;");
        builder.AppendLine("        Dispose();");
        builder.AppendLine("        return Task.CompletedTask;");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    public void Dispose()");
        builder.AppendLine("    {");
        builder.AppendLine("        subscription?.Dispose();");
        builder.AppendLine("        subscription = null;");
        builder.AppendLine("    }");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderQueuedMonitorSubscription(
        DotNetConfigurationBinding binding,
        string subscriptionName)
    {
        var definition = binding.Definition;
        var typeName = definition.TypeName;
        var consumerName = string.Concat("I", typeName, "ChangeConsumer");
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine("using System.Threading.Channels;");
        builder.AppendLine("using Microsoft.Extensions.Hosting;");
        builder.AppendLine("using Microsoft.Extensions.Logging;");
        builder.AppendLine("using Microsoft.Extensions.Options;");
        builder.AppendLine();
        builder.Append("namespace ").Append(definition.Namespace).AppendLine(";");
        builder.AppendLine();
        builder.AppendLine("/// <summary>Queues validated monitored Options for consumer-owned reactions.</summary>");
        builder
            .Append("public sealed class ")
            .Append(subscriptionName)
            .AppendLine(" : BackgroundService");
        builder.AppendLine("{");
        builder
            .Append("    private readonly IEnumerable<")
            .Append(consumerName)
            .AppendLine("> consumers;");
        builder
            .Append("    private readonly IOptionsMonitor<")
            .Append(typeName)
            .AppendLine("> monitor;");
        builder
            .Append("    private readonly ILogger<")
            .Append(typeName)
            .AppendLine("> logger;");
        builder
            .Append("    private readonly Channel<(")
            .Append(typeName)
            .AppendLine(" Value, string Name)> changes =");
        builder
            .Append("        Channel.CreateBounded<(")
            .Append(typeName)
            .AppendLine(" Value, string Name)>(new BoundedChannelOptions(1)");
        builder.AppendLine("        {");
        builder.AppendLine("            FullMode = BoundedChannelFullMode.DropOldest,");
        builder.AppendLine("            SingleReader = true,");
        builder.AppendLine("            SingleWriter = false,");
        builder.AppendLine("        });");
        builder.AppendLine("    private IDisposable? subscription;");
        builder.AppendLine();
        builder.AppendLine("    /// <summary>Initializes the bounded queue with framework and consumer-owned dependencies.</summary>");
        builder
            .Append("    public ")
            .Append(subscriptionName)
            .Append("(IOptionsMonitor<")
            .Append(typeName)
            .Append("> monitor, IEnumerable<")
            .Append(consumerName)
            .Append(" > consumers, ILogger<")
            .Append(typeName)
            .AppendLine("> logger)");
        builder.AppendLine("    {");
        builder.AppendLine("        this.monitor = monitor;");
        builder.AppendLine("        this.consumers = consumers;");
        builder.AppendLine("        this.logger = logger;");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    public override Task StartAsync(CancellationToken cancellationToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        subscription = monitor.OnChange((value, optionsName) =>");
        builder.AppendLine("        {");
        builder.AppendLine("            var normalizedOptionsName = optionsName ?? Options.DefaultName;");
        builder
            .Append("            if (!string.Equals(normalizedOptionsName, ")
            .Append(DotNetSourceText.CSharpLiteral(binding.OptionsName))
            .AppendLine(", StringComparison.Ordinal))");
        builder.AppendLine("            {");
        builder.AppendLine("                return;");
        builder.AppendLine("            }");
        builder.AppendLine("            changes.Writer.TryWrite((value, normalizedOptionsName));");
        builder
            .Append("            logger.LogInformation(")
            .Append(DotNetSourceText.CSharpLiteral(
                "Validated configuration change queued for {DefinitionIdentity} and Options name {OptionsName}; values and references are redacted."))
            .Append(", ")
            .Append(DotNetSourceText.CSharpLiteral(definition.Identity.Value))
            .AppendLine(", normalizedOptionsName);");
        builder.AppendLine("        });");
        builder.AppendLine("        return base.StartAsync(cancellationToken);");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    protected override async Task ExecuteAsync(CancellationToken stoppingToken)");
        builder.AppendLine("    {");
        builder.AppendLine("        await foreach (var change in changes.Reader.ReadAllAsync(stoppingToken))");
        builder.AppendLine("        {");
        builder.AppendLine("            foreach (var consumer in consumers)");
        builder.AppendLine("            {");
        builder.AppendLine("                await consumer.ConsumeAsync(change.Value, change.Name, stoppingToken);");
        builder.AppendLine("            }");
        builder.AppendLine("        }");
        builder.AppendLine("    }");
        builder.AppendLine();
        builder.AppendLine("    /// <inheritdoc />");
        builder.AppendLine("    public override void Dispose()");
        builder.AppendLine("    {");
        builder.AppendLine("        subscription?.Dispose();");
        builder.AppendLine("        subscription = null;");
        builder.AppendLine("        changes.Writer.TryComplete();");
        builder.AppendLine("        base.Dispose();");
        builder.AppendLine("    }");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderChangeConsumer(
        DotNetConfigurationDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine();
        builder.Append("namespace ").Append(definition.Namespace).AppendLine(";");
        builder.AppendLine();
        builder.AppendLine("/// <summary>Consumer-owned reaction to one validated monitored Options value.</summary>");
        builder
            .Append("public interface I")
            .Append(definition.TypeName)
            .AppendLine("ChangeConsumer");
        builder.AppendLine("{");
        builder.AppendLine("    /// <summary>Consumes one bounded queued change without transferring reaction meaning to Program Kit.</summary>");
        builder
            .Append("    ValueTask ConsumeAsync(")
            .Append(definition.TypeName)
            .AppendLine(" value, string optionsName, CancellationToken cancellationToken);");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string MonitorSubscriptionName(
        DotNetConfigurationBinding binding)
    {
        if (string.IsNullOrEmpty(binding.OptionsName))
        {
            return string.Concat(
                binding.Definition.TypeName,
                "MonitorSubscription");
        }

        var digest = Convert.ToHexStringLower(
            SHA256.HashData(Encoding.UTF8.GetBytes(binding.OptionsName)));
        return string.Concat(
            binding.Definition.TypeName,
            "Named",
            digest,
            "MonitorSubscription");
    }

    private static string RenderConfiguration(
        ImmutableArray<DotNetConfigurationBinding> bindings,
        bool examples)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        var definitions = bindings
            .Select(static binding => binding.Definition)
            .DistinctBy(static definition => string.Concat(
                definition.Identity.Value,
                "@",
                definition.Version.Value))
            .OrderBy(static definition => definition.Section, StringComparer.Ordinal)
            .ToArray();
        for (var definitionIndex = 0;
             definitionIndex < definitions.Length;
             definitionIndex++)
        {
            var definition = definitions[definitionIndex];
            builder
                .Append("  ")
                .Append(DotNetSourceText.JsonLiteral(definition.Section))
                .AppendLine(": {");
            var properties = definition.Properties
                .Where(static property =>
                    property.Classification == DotNetConfigurationValueClassification.Public)
                .Select(property => new
                {
                    Property = property,
                    Value = examples
                        ? property.ExampleValue ?? property.DefaultValue
                        : property.DefaultValue,
                })
                .Where(static item => item.Value is not null)
                .ToArray();
            for (var propertyIndex = 0;
                 propertyIndex < properties.Length;
                 propertyIndex++)
            {
                var item = properties[propertyIndex];
                builder
                    .Append("    ")
                    .Append(DotNetSourceText.JsonLiteral(item.Property.Key))
                    .Append(": ")
                    .Append(JsonValue(item.Property.ValueKind, item.Value!))
                    .AppendLine(propertyIndex == properties.Length - 1 ? string.Empty : ",");
            }

            builder
                .Append("  }")
                .AppendLine(definitionIndex == definitions.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderDeveloperOverlay(
        ImmutableArray<DotNetConfigurationBinding> bindings)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        var sections = bindings
            .Select(static binding => binding.Definition.Section)
            .Distinct(StringComparer.Ordinal)
            .Order(StringComparer.Ordinal)
            .ToArray();
        for (var index = 0; index < sections.Length; index++)
        {
            builder
                .Append("  ")
                .Append(DotNetSourceText.JsonLiteral(sections[index]))
                .Append(": {}")
                .AppendLine(index == sections.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderEnvironmentMap(
        ImmutableArray<DotNetConfigurationBinding> bindings)
    {
        var entries = bindings
            .Select(static binding => binding.Definition)
            .DistinctBy(static definition => string.Concat(
                definition.Identity.Value,
                "@",
                definition.Version.Value))
            .SelectMany(definition => definition.Properties.Select(property =>
                new
                {
                    Name = string.Concat(
                        definition.Section,
                        "__",
                        property.Key),
                    property.Classification,
                }))
            .OrderBy(static item => item.Name, StringComparer.Ordinal)
            .ToArray();
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"entries\": [");
        for (var index = 0; index < entries.Length; index++)
        {
            var entry = entries[index];
            builder
                .Append("    {\"name\": ")
                .Append(DotNetSourceText.JsonLiteral(entry.Name))
                .Append(", \"classification\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(entry.Classification)))
                .Append('}')
                .AppendLine(index == entries.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ]");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderKeyPerFileMap(
        ImmutableArray<DotNetConfigurationBinding> bindings)
    {
        var paths = bindings
            .Select(static binding => binding.Definition)
            .DistinctBy(static definition => string.Concat(
                definition.Identity.Value,
                "@",
                definition.Version.Value))
            .SelectMany(definition => definition.Properties.Select(property =>
                string.Concat(definition.Section, "__", property.Key)))
            .Order(StringComparer.Ordinal)
            .ToArray();
        return RenderStringArray("paths", paths);
    }

    private static string RenderProviderBindings(
        ImmutableArray<DotNetConfigurationSource> sources)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"precedence\": \"later-source-wins\",");
        builder.AppendLine("  \"sources\": [");
        for (var index = 0; index < sources.Length; index++)
        {
            var source = sources[index];
            builder
                .Append("    {\"identity\": ")
                .Append(DotNetSourceText.JsonLiteral(source.Identity.Value))
                .Append(", \"order\": ")
                .Append(source.Order.ToString(CultureInfo.InvariantCulture))
                .Append(", \"providerKind\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(source.ProviderKind)))
                .Append(", \"providerRevision\": ")
                .Append(DotNetSourceText.JsonLiteral(string.Concat(
                    source.ProviderRevision.Identity.Value,
                    "@",
                    source.ProviderRevision.Version.Value,
                    "#",
                    source.ProviderRevision.Digest.Value)))
                .Append(", \"package\": ")
                .Append(DotNetSourceText.JsonLiteral(string.Concat(
                    source.Package.PackageId,
                    "@",
                    source.Package.Version.Value,
                    "#",
                    source.Package.Sha256.Value)))
                .Append(", \"path\": ")
                .Append(source.Path is null
                    ? "null"
                    : DotNetSourceText.JsonLiteral(source.Path))
                .Append(", \"prefix\": ")
                .Append(source.Prefix is null
                    ? "null"
                    : DotNetSourceText.JsonLiteral(source.Prefix))
                .Append(", \"optional\": ")
                .Append(source.Optional ? "true" : "false")
                .Append(", \"startupDisposition\": ")
                .Append(DotNetSourceText.JsonLiteral(
                    EnumText(source.StartupDisposition)))
                .Append(", \"reload\": ")
                .Append(source.Reload.Enabled ? "true" : "false")
                .Append(", \"reloadCapability\": ")
                .Append(DotNetSourceText.JsonLiteral(
                    EnumText(source.Reload.Capability)))
                .Append(", \"pollIntervalSeconds\": ")
                .Append(source.Reload.PollIntervalSeconds?.ToString(
                    CultureInfo.InvariantCulture) ?? "null")
                .Append(", \"refreshRevision\": ")
                .Append(source.Reload.RefreshRevision is null
                    ? "null"
                    : DotNetSourceText.JsonLiteral(string.Concat(
                        source.Reload.RefreshRevision.Identity.Value,
                        "@",
                        source.Reload.RefreshRevision.Version.Value,
                        "#",
                        source.Reload.RefreshRevision.Digest.Value)))
                .Append(", \"secretClassification\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(source.SecretClassification)))
                .Append(", \"failureDisposition\": ")
                .Append(DotNetSourceText.JsonLiteral(
                    EnumText(source.FailureDisposition)))
                .Append('}')
                .AppendLine(index == sources.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ]");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderValidationReport(
        ImmutableArray<DotNetConfigurationBinding> bindings)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"bindings\": [");
        for (var index = 0; index < bindings.Length; index++)
        {
            var binding = bindings[index];
            builder
                .Append("    {\"definition\": ")
                .Append(DotNetSourceText.JsonLiteral(binding.Definition.Identity.Value))
                .Append(", \"definitionVersion\": ")
                .Append(DotNetSourceText.JsonLiteral(binding.Definition.Version.Value))
                .Append(", \"owner\": ")
                .Append(DotNetSourceText.JsonLiteral(binding.Definition.OwnerIdentity.Value))
                .Append(", \"ownerKind\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(binding.Definition.OwnerKind)))
                .Append(", \"schemaRevision\": ")
                .Append(DotNetSourceText.JsonLiteral(
                    string.Concat(
                        binding.Definition.SchemaRevision.Identity.Value,
                        "@",
                        binding.Definition.SchemaRevision.Version.Value,
                        "#",
                        binding.Definition.SchemaRevision.Digest.Value)))
                .Append(", \"compatibilityPolicy\": ")
                .Append(DotNetSourceText.JsonLiteral(
                    binding.Definition.Compatibility.Policy.Value))
                .Append(", \"optionsName\": ")
                .Append(DotNetSourceText.JsonLiteral(binding.OptionsName))
                .Append(", \"validateOnStart\": ")
                .Append(binding.ValidateOnStart ? "true" : "false")
                .Append(", \"securityCritical\": ")
                .Append(binding.SecurityCritical ? "true" : "false")
                .Append(", \"consumption\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(binding.Consumption)))
                .Append(", \"consumerLifetime\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(binding.ConsumerLifetime)))
                .Append(", \"changeReaction\": ")
                .Append(DotNetSourceText.JsonLiteral(EnumText(binding.ChangeReaction)))
                .Append(", \"restartRequired\": ")
                .Append(binding.RestartRequired ? "true" : "false")
                .Append(", \"invalidReloadPolicy\": \"framework-validation-failure-no-retention-claim\"}")
                .AppendLine(index == bindings.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ]");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderProvenance(DotNetHostDefinition host) =>
        string.Concat(
            "{\n",
            "  \"design\": \"pkid:design:program-kit:host-tooling@1.3.0#sha256:a9ad015470f3996ea09811d57007ec4ab90e3b2cbff91245e625bfdd82ad0d57\",\n",
            "  \"plan\": \"pkid:plan:program-kit:host-tooling@1.3.0#sha256:8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5\",\n",
            "  \"workUnit\": \"W020\",\n",
            "  \"host\": ",
            DotNetSourceText.JsonLiteral(host.Identity.Value),
            "\n}\n");

    private static string RenderOwnership(
        ImmutableArray<DotNetConfigurationSource> sources)
    {
        var generated = new List<string>
        {
            "ProgramKitGenerated/Configuration/",
            "configuration/generated/",
            "configuration/examples/",
            "configuration/environment-map.json",
            "configuration/key-per-file-map.json",
            "configuration/provider-bindings.json",
            "configuration/validation-report.json",
            "configuration/provenance.json",
            "configuration/ownership.json",
        };
        generated.AddRange(sources
            .Where(static source =>
                source.ProviderKind ==
                DotNetConfigurationProviderKind.JsonFile)
            .Select(static source => source.Path!));
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"generated\": [");
        for (var index = 0; index < generated.Count; index++)
        {
            builder
                .Append("    ")
                .Append(DotNetSourceText.JsonLiteral(generated[index]))
                .AppendLine(index == generated.Count - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ],");
        builder.AppendLine("  \"human\": [");
        builder.AppendLine("    \"configuration/developer/appsettings.Development.json\"");
        builder.AppendLine("  ],");
        builder.AppendLine("  \"collisionPolicy\": \"fail-never-merge-or-overwrite\"");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderStringArray(string name, string[] values)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder
            .Append("  ")
            .Append(DotNetSourceText.JsonLiteral(name))
            .AppendLine(": [");
        for (var index = 0; index < values.Length; index++)
        {
            builder
                .Append("    ")
                .Append(DotNetSourceText.JsonLiteral(values[index]))
                .AppendLine(index == values.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ]");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string JsonValue(
        DotNetConfigurationValueKind kind,
        string value) =>
        kind switch
        {
            DotNetConfigurationValueKind.Boolean => value.ToLowerInvariant(),
            DotNetConfigurationValueKind.WholeNumber32 or
                DotNetConfigurationValueKind.WholeNumber64 or
                DotNetConfigurationValueKind.DecimalNumber or
                DotNetConfigurationValueKind.FloatingPoint => value,
            _ => DotNetSourceText.JsonLiteral(value),
        };

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

    private static GeneratedOutput Output(string path, string text) =>
        new(path, DotNetSourceText.Utf8(text));
}
