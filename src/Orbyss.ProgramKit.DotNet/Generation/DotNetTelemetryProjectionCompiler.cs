using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Deterministic provider-neutral emission and pinned OpenTelemetry adapter compiler.</summary>
public sealed class DotNetTelemetryProjectionCompiler :
    IDotNetTelemetryProjectionCompiler
{
    /// <inheritdoc />
    public ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        if (host.Telemetry is null)
        {
            return [];
        }

        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        outputs.Add(new GeneratedOutput(
            "ProgramKitGenerated/Hosting/ProgramKitTelemetry.cs",
            DotNetSourceText.Utf8(RenderTelemetry(host.Telemetry))));
        foreach (var category in host.Telemetry.LoggerEvents
                     .Select(static item => item.Category)
                     .Distinct(StringComparer.Ordinal)
                     .Order(StringComparer.Ordinal))
        {
            outputs.Add(new GeneratedOutput(
                string.Concat(
                    "ProgramKitGenerated/Hosting/",
                    Category(category),
                    ".cs"),
                DotNetSourceText.Utf8(RenderCategory(category))));
        }

        if (host.Telemetry.OtlpExporter is not null)
        {
            outputs.Add(new GeneratedOutput(
                "ProgramKitGenerated/Hosting/ProgramKitTelemetryOptions.cs",
                DotNetSourceText.Utf8(RenderTelemetryOptions())));
        }

        return outputs.ToImmutable();
    }

    /// <inheritdoc />
    public string RenderRegistration(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        var telemetry = host.Telemetry;
        if (telemetry is null)
        {
            return string.Empty;
        }

        var builder = new StringBuilder();
        if (telemetry.OtlpExporter is not null)
        {
            builder
                .Append("var programKitTelemetryEndpoint = global::GeneratedHost.Hosting.ProgramKitTelemetryOptions.ParseEndpoint(builder.Configuration[")
                .Append(DotNetSourceText.CSharpLiteral(
                    telemetry.OtlpExporter.EndpointConfigurationKey))
                .AppendLine("]);");
            builder.AppendLine("builder.Services.AddOptions<global::GeneratedHost.Hosting.ProgramKitTelemetryOptions>()");
            builder.AppendLine("    .Configure(options => options.Endpoint = programKitTelemetryEndpoint)");
            builder.AppendLine("    .Validate(static options => options.Endpoint.IsAbsoluteUri, \"The OTLP endpoint must be absolute.\")");
            builder.AppendLine("    .ValidateOnStart();");
        }

        if (telemetry.LoggingFilterConfigurationKey is not null)
        {
            builder.AppendLine("builder.Logging.AddConfiguration(builder.Configuration.GetSection(\"Logging\"));");
        }

        builder
            .Append("builder.Services.Configure<global::Microsoft.Extensions.Hosting.HostOptions>(options => options.ShutdownTimeout = global::System.TimeSpan.FromMilliseconds(")
            .Append(telemetry.ShutdownTimeoutMilliseconds)
            .AppendLine("));");
        builder.AppendLine("global::System.Diagnostics.Activity.DefaultIdFormat = global::System.Diagnostics.ActivityIdFormat.W3C;");
        builder.AppendLine("global::System.Diagnostics.Activity.ForceDefaultIdFormat = true;");
        builder.AppendLine("global::OpenTelemetry.Sdk.SetDefaultTextMapPropagator(new global::OpenTelemetry.Context.Propagation.TraceContextPropagator());");
        builder.AppendLine("builder.Logging.AddJsonConsole();");
        builder.AppendLine("var openTelemetry = builder.Services.AddOpenTelemetry()");
        builder
            .Append("    .ConfigureResource(resource => resource.AddService(")
            .Append(DotNetSourceText.CSharpLiteral(telemetry.Resource.ServiceName))
            .Append(", ")
            .Append(DotNetSourceText.CSharpLiteral(telemetry.Resource.ServiceNamespace))
            .Append(", ")
            .Append(DotNetSourceText.CSharpLiteral(telemetry.Resource.ServiceVersion.Value))
            .AppendLine("))");
        RenderTracing(builder, telemetry);
        RenderMetrics(builder, telemetry);
        RenderLogging(builder, telemetry);
        builder.AppendLine(";");
        builder.AppendLine("_ = openTelemetry;");
        return builder.ToString();
    }

    /// <inheritdoc />
    public string RenderMiddleware(DotNetHostDefinition host)
    {
        ArgumentNullException.ThrowIfNull(host);
        return host.Telemetry?.HttpDiagnostics.Enabled == true
            ? "app.UseHttpLogging();" + Environment.NewLine
            : string.Empty;
    }

    private static void RenderTracing(
        StringBuilder builder,
        DotNetTelemetryConfiguration telemetry)
    {
        builder.AppendLine("    .WithTracing(tracing =>");
        builder.AppendLine("    {");
        foreach (var source in telemetry.Activities
                     .Select(static activity => activity.SourceName)
                     .Distinct(StringComparer.Ordinal)
                     .Order(StringComparer.Ordinal))
        {
            builder
                .Append("        tracing.AddSource(")
                .Append(DotNetSourceText.CSharpLiteral(source))
                .AppendLine(");");
        }

        builder.Append("        tracing.SetSampler(")
            .Append(Sampler(telemetry.Sampling))
            .AppendLine(");");
        foreach (var instrumentation in telemetry.Instrumentations
                     .Where(static item => item.Traces)
                     .OrderBy(static item => item.Kind))
        {
            if (instrumentation.Kind == DotNetTelemetryInstrumentationKind.AspNetCore)
            {
                builder.AppendLine("        tracing.AddAspNetCoreInstrumentation(options =>");
                builder.AppendLine("        {");
                builder
                    .Append("            options.RecordException = ")
                    .Append(instrumentation.RecordExceptions ? "true" : "false")
                    .AppendLine(";");
                builder.AppendLine("        });");
            }
            else
            {
                builder.AppendLine("        tracing.AddHttpClientInstrumentation();");
            }
        }

        if (telemetry.OtlpExporter is not null)
        {
            RenderTraceExporter(builder, telemetry.OtlpExporter);
        }

        builder.AppendLine("    })");
    }

    private static void RenderMetrics(
        StringBuilder builder,
        DotNetTelemetryConfiguration telemetry)
    {
        builder.AppendLine("    .WithMetrics(metrics =>");
        builder.AppendLine("    {");
        foreach (var meter in telemetry.Metrics
                     .Select(static metric => metric.MeterName)
                     .Distinct(StringComparer.Ordinal)
                     .Order(StringComparer.Ordinal))
        {
            builder
                .Append("        metrics.AddMeter(")
                .Append(DotNetSourceText.CSharpLiteral(meter))
                .AppendLine(");");
        }

        foreach (var instrumentation in telemetry.Instrumentations
                     .Where(static item => item.Metrics)
                     .OrderBy(static item => item.Kind))
        {
            builder.AppendLine(instrumentation.Kind ==
                               DotNetTelemetryInstrumentationKind.AspNetCore
                ? "        metrics.AddAspNetCoreInstrumentation();"
                : "        metrics.AddHttpClientInstrumentation();");
        }

        if (telemetry.OtlpExporter is not null)
        {
            RenderMetricExporter(builder, telemetry.OtlpExporter);
        }

        builder.AppendLine("    })");
    }

    private static void RenderLogging(
        StringBuilder builder,
        DotNetTelemetryConfiguration telemetry)
    {
        builder.AppendLine("    .WithLogging(logging =>");
        builder.AppendLine("    {");
        if (telemetry.OtlpExporter is not null)
        {
            RenderLogExporter(builder, telemetry.OtlpExporter);
        }

        builder.AppendLine("    }, options =>");
        builder.AppendLine("    {");
        builder.AppendLine("        options.IncludeFormattedMessage = false;");
        builder.AppendLine("        options.IncludeScopes = true;");
        builder.AppendLine("        options.ParseStateValues = true;");
        builder.AppendLine("    })");
    }

    private static void RenderTraceExporter(
        StringBuilder builder,
        DotNetOtlpExporter exporter)
    {
        builder.AppendLine("        tracing.AddOtlpExporter(options =>");
        builder.AppendLine("        {");
        RenderExporterOptions(builder, exporter, "            ");
        builder.AppendLine("            options.ExportProcessorType = global::OpenTelemetry.ExportProcessorType.Batch;");
        builder
            .Append("            options.BatchExportProcessorOptions.MaxQueueSize = ")
            .Append(exporter.MaxQueueSize)
            .AppendLine(";");
        builder
            .Append("            options.BatchExportProcessorOptions.MaxExportBatchSize = ")
            .Append(exporter.MaxExportBatchSize)
            .AppendLine(";");
        builder
            .Append("            options.BatchExportProcessorOptions.ScheduledDelayMilliseconds = ")
            .Append(exporter.ScheduledDelayMilliseconds)
            .AppendLine(";");
        builder
            .Append("            options.BatchExportProcessorOptions.ExporterTimeoutMilliseconds = ")
            .Append(exporter.ExportTimeoutMilliseconds)
            .AppendLine(";");
        builder.AppendLine("        });");
    }

    private static void RenderMetricExporter(
        StringBuilder builder,
        DotNetOtlpExporter exporter)
    {
        builder.AppendLine("        metrics.AddOtlpExporter((options, reader) =>");
        builder.AppendLine("        {");
        RenderExporterOptions(builder, exporter, "            ");
        builder
            .Append("            reader.PeriodicExportingMetricReaderOptions.ExportIntervalMilliseconds = ")
            .Append(exporter.ScheduledDelayMilliseconds)
            .AppendLine(";");
        builder
            .Append("            reader.PeriodicExportingMetricReaderOptions.ExportTimeoutMilliseconds = ")
            .Append(exporter.ExportTimeoutMilliseconds)
            .AppendLine(";");
        builder.AppendLine("        });");
    }

    private static void RenderLogExporter(
        StringBuilder builder,
        DotNetOtlpExporter exporter)
    {
        builder.AppendLine("        logging.AddOtlpExporter((options, processor) =>");
        builder.AppendLine("        {");
        RenderExporterOptions(builder, exporter, "            ");
        builder
            .Append("            processor.BatchExportProcessorOptions.MaxQueueSize = ")
            .Append(exporter.MaxQueueSize)
            .AppendLine(";");
        builder
            .Append("            processor.BatchExportProcessorOptions.MaxExportBatchSize = ")
            .Append(exporter.MaxExportBatchSize)
            .AppendLine(";");
        builder
            .Append("            processor.BatchExportProcessorOptions.ScheduledDelayMilliseconds = ")
            .Append(exporter.ScheduledDelayMilliseconds)
            .AppendLine(";");
        builder
            .Append("            processor.BatchExportProcessorOptions.ExporterTimeoutMilliseconds = ")
            .Append(exporter.ExportTimeoutMilliseconds)
            .AppendLine(";");
        builder.AppendLine("        });");
    }

    private static void RenderExporterOptions(
        StringBuilder builder,
        DotNetOtlpExporter exporter,
        string indent)
    {
        builder
            .Append(indent)
            .AppendLine("options.Endpoint = programKitTelemetryEndpoint;");
        builder
            .Append(indent)
            .Append("options.Protocol = global::OpenTelemetry.Exporter.OtlpExportProtocol.")
            .Append(exporter.Protocol)
            .AppendLine(";");
        builder
            .Append(indent)
            .Append("options.TimeoutMilliseconds = ")
            .Append(exporter.ExportTimeoutMilliseconds)
            .AppendLine(";");
    }

    private static string Sampler(DotNetTelemetrySampling sampling) =>
        sampling.Kind switch
        {
            DotNetTelemetrySamplerKind.AlwaysOn =>
                "new global::OpenTelemetry.Trace.AlwaysOnSampler()",
            DotNetTelemetrySamplerKind.AlwaysOff =>
                "new global::OpenTelemetry.Trace.AlwaysOffSampler()",
            DotNetTelemetrySamplerKind.ParentBasedTraceIdRatio =>
                string.Concat(
                    "new global::OpenTelemetry.Trace.ParentBasedSampler(new global::OpenTelemetry.Trace.TraceIdRatioBasedSampler(",
                    sampling.Ratio!.Value.ToString("R", CultureInfo.InvariantCulture),
                    "))"),
            _ => throw new ArgumentOutOfRangeException(nameof(sampling)),
        };

    private static string RenderTelemetryOptions() =>
        """
        // <auto-generated program-kit>
        #nullable enable

        namespace GeneratedHost.Hosting;

        /// <summary>Startup-fixed, validated options for reviewed telemetry export.</summary>
        public sealed class ProgramKitTelemetryOptions
        {
            /// <summary>Gets or sets the absolute OTLP collector endpoint.</summary>
            public Uri Endpoint { get; set; } = null!;

            /// <summary>Parses the required endpoint without exposing secret-bearing configuration.</summary>
            public static Uri ParseEndpoint(string? value)
            {
                if (!Uri.TryCreate(value, UriKind.Absolute, out var endpoint) ||
                    (endpoint.Scheme != Uri.UriSchemeHttp &&
                     endpoint.Scheme != Uri.UriSchemeHttps))
                {
                    throw new global::Microsoft.Extensions.Options.OptionsValidationException(
                        "ProgramKitTelemetry",
                        typeof(ProgramKitTelemetryOptions),
                        ["The OTLP endpoint configuration reference must be an absolute HTTP or HTTPS URI."]);
                }

                return endpoint;
            }
        }
        """;

    private static string RenderTelemetry(DotNetTelemetryConfiguration telemetry)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine("using System.Diagnostics;");
        builder.AppendLine("using System.Diagnostics.Metrics;");
        builder.AppendLine("using Microsoft.Extensions.Logging;");
        builder.AppendLine();
        builder.AppendLine("namespace GeneratedHost.Hosting;");
        builder.AppendLine();
        builder.AppendLine("/// <summary>Stable provider-neutral telemetry emission surface.</summary>");
        builder.AppendLine("public static partial class ProgramKitTelemetry");
        builder.AppendLine("{");
        foreach (var activityGroup in telemetry.Activities
                     .GroupBy(static item => (item.SourceName, item.SourceVersion.Value))
                     .OrderBy(static group => group.Key.SourceName, StringComparer.Ordinal))
        {
            builder
                .Append("    private static readonly ActivitySource ")
                .Append(Field(activityGroup.Key.SourceName))
                .Append(" = new(")
                .Append(DotNetSourceText.CSharpLiteral(activityGroup.Key.SourceName))
                .Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(activityGroup.Key.Value))
                .AppendLine(");");
        }

        foreach (var metricGroup in telemetry.Metrics
                     .GroupBy(static item => (item.MeterName, item.MeterVersion.Value))
                     .OrderBy(static group => group.Key.MeterName, StringComparer.Ordinal))
        {
            builder
                .Append("    private static readonly Meter ")
                .Append(Field(metricGroup.Key.MeterName))
                .Append(" = new(")
                .Append(DotNetSourceText.CSharpLiteral(metricGroup.Key.MeterName))
                .Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(metricGroup.Key.Value))
                .AppendLine(");");
        }

        foreach (var metric in telemetry.Metrics.OrderBy(static item => item.Name, StringComparer.Ordinal))
        {
            builder
                .Append("    private static readonly ")
                .Append(metric.Kind == DotNetMetricInstrumentKind.Counter
                    ? "Counter<long>"
                    : "Histogram<double>")
                .Append(' ')
                .Append(Field(metric.Name))
                .Append(" = ")
                .Append(Field(metric.MeterName))
                .Append(metric.Kind == DotNetMetricInstrumentKind.Counter
                    ? ".CreateCounter<long>("
                    : ".CreateHistogram<double>(")
                .Append(DotNetSourceText.CSharpLiteral(metric.Name))
                .Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(metric.Unit))
                .Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(metric.Description))
                .AppendLine(");");
        }

        builder.AppendLine();
        foreach (var loggerEvent in telemetry.LoggerEvents.OrderBy(static item => item.EventId))
        {
            builder
                .Append("    [LoggerMessage(EventId = ")
                .Append(loggerEvent.EventId)
                .Append(", EventName = ")
                .Append(DotNetSourceText.CSharpLiteral(loggerEvent.EventName))
                .Append(", Level = LogLevel.")
                .Append(loggerEvent.Level)
                .Append(", Message = ")
                .Append(DotNetSourceText.CSharpLiteral(loggerEvent.MessageTemplate))
                .AppendLine(")]");
            builder
                .Append("    public static partial void ")
                .Append(loggerEvent.EventName)
                .Append("(ILogger<")
                .Append(Category(loggerEvent.Category))
                .Append("> logger");
            foreach (var field in loggerEvent.ScopeFields)
            {
                builder.Append(", string ").Append(Parameter(field));
            }

            builder.AppendLine(");");
            if (!loggerEvent.ScopeFields.IsEmpty)
            {
                builder
                    .Append("    public static IDisposable? Begin")
                    .Append(loggerEvent.EventName)
                    .Append("Scope(ILogger<")
                    .Append(Category(loggerEvent.Category))
                    .Append("> logger");
                foreach (var field in loggerEvent.ScopeFields)
                {
                    builder.Append(", string ").Append(Parameter(field));
                }

                builder.AppendLine(") => logger.BeginScope(new Dictionary<string, object?>");
                builder.AppendLine("    {");
                foreach (var field in loggerEvent.ScopeFields)
                {
                    builder
                        .Append("        [")
                        .Append(DotNetSourceText.CSharpLiteral(field))
                        .Append("] = ")
                        .Append(Parameter(field))
                        .AppendLine(",");
                }

                builder.AppendLine("    });");
            }
        }

        foreach (var activity in telemetry.Activities.OrderBy(static item => item.Name, StringComparer.Ordinal))
        {
            builder
                .Append("    public static Activity? Start")
                .Append(Method(activity.Name))
                .Append('(');
            RenderAttributeParameters(builder, activity.Attributes);
            builder.AppendLine(")");
            builder.AppendLine("    {");
            RenderAttributeValidation(builder, activity.Attributes, "        ");
            builder
                .Append("        var activity = ")
                .Append(Field(activity.SourceName))
                .Append(".StartActivity(")
                .Append(DotNetSourceText.CSharpLiteral(activity.Name))
                .Append(", ActivityKind.")
                .Append(activity.Kind)
                .AppendLine(");");
            foreach (var attribute in activity.Attributes)
            {
                builder
                    .Append("        activity?.SetTag(")
                    .Append(DotNetSourceText.CSharpLiteral(attribute.Name))
                    .Append(", ")
                    .Append(Parameter(attribute.Name))
                    .AppendLine(");");
            }

            builder.AppendLine("        return activity;");
            builder.AppendLine("    }");
        }

        foreach (var metric in telemetry.Metrics.OrderBy(static item => item.Name, StringComparer.Ordinal))
        {
            builder
                .Append("    public static void Record")
                .Append(Method(metric.Name))
                .Append(metric.Kind == DotNetMetricInstrumentKind.Counter
                    ? "(long value"
                    : "(double value");
            if (!metric.Attributes.IsEmpty)
            {
                builder.Append(", ");
                RenderAttributeParameters(builder, metric.Attributes);
            }

            builder.AppendLine(")");
            builder.AppendLine("    {");
            RenderAttributeValidation(builder, metric.Attributes, "        ");
            if (!metric.Attributes.IsEmpty)
            {
                builder.AppendLine("        TagList tags = default;");
                foreach (var attribute in metric.Attributes)
                {
                    builder
                        .Append("        tags.Add(")
                        .Append(DotNetSourceText.CSharpLiteral(attribute.Name))
                        .Append(", ")
                        .Append(Parameter(attribute.Name))
                        .AppendLine(");");
                }
            }

            builder
                .Append("        ")
                .Append(Field(metric.Name))
                .Append(metric.Kind == DotNetMetricInstrumentKind.Counter
                    ? ".Add(value"
                    : ".Record(value")
                .Append(metric.Attributes.IsEmpty ? ");" : ", in tags);")
                .AppendLine();
            builder.AppendLine("    }");
        }

        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderCategory(string category)
    {
        var typeName = Category(category);
        return string.Concat(
            "// <auto-generated program-kit>",
            Environment.NewLine,
            "#nullable enable",
            Environment.NewLine,
            Environment.NewLine,
            "namespace GeneratedHost.Hosting;",
            Environment.NewLine,
            Environment.NewLine,
            "/// <summary>Stable typed logger category selected by ",
            category,
            ".</summary>",
            Environment.NewLine,
            "public sealed class ",
            typeName,
            Environment.NewLine,
            "{",
            Environment.NewLine,
            "    private ",
            typeName,
            "() { }",
            Environment.NewLine,
            "}",
            Environment.NewLine);
    }

    private static void RenderAttributeParameters(
        StringBuilder builder,
        ImmutableArray<DotNetTelemetryAttributeDefinition> attributes)
    {
        for (var index = 0; index < attributes.Length; index++)
        {
            if (index > 0)
            {
                builder.Append(", ");
            }

            builder
                .Append("string ")
                .Append(Parameter(attributes[index].Name));
        }
    }

    private static void RenderAttributeValidation(
        StringBuilder builder,
        ImmutableArray<DotNetTelemetryAttributeDefinition> attributes,
        string indent)
    {
        foreach (var attribute in attributes)
        {
            builder
                .Append(indent)
                .Append("if (")
                .Append(Parameter(attribute.Name))
                .Append(" is not (")
                .Append(string.Join(
                    " or ",
                    attribute.AllowedValues
                        .Order(StringComparer.Ordinal)
                        .Select(DotNetSourceText.CSharpLiteral)))
                .AppendLine("))");
            builder.Append(indent).AppendLine("{");
            builder
                .Append(indent)
                .Append("    throw new ArgumentOutOfRangeException(nameof(")
                .Append(Parameter(attribute.Name))
                .AppendLine("), \"The telemetry attribute value is outside its reviewed bounded catalog.\");");
            builder.Append(indent).AppendLine("}");
        }
    }

    private static string Field(string value) =>
        string.Concat("_", Parameter(value));

    private static string Method(string value)
    {
        var identifier = string.Concat(
            value.Split(['.', '-', '_'], StringSplitOptions.RemoveEmptyEntries)
                .Select(static part =>
                    string.Concat(char.ToUpperInvariant(part[0]), part[1..])));
        return char.IsLetter(identifier[0]) || identifier[0] == '_'
            ? identifier
            : string.Concat("N", identifier);
    }

    private static string Category(string value) =>
        string.Concat(Method(value), "Category");

    private static string Parameter(string value)
    {
        var method = Method(value);
        return string.Concat(char.ToLowerInvariant(method[0]), method[1..]);
    }
}
