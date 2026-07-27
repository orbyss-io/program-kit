using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>
/// Deterministic Aspire AppHost source projection. It never restores, runs,
/// deploys, discovers, or reads the referenced resources.
/// </summary>
public sealed class AspireAppHostGenerator : IAspireAppHostGenerator
{
    private const string AspireVersion = "13.4.6";
    private const string DotNetSdkVersion = "10.0.302";
    private const string TargetFramework = "net10.0";
    private const string AspireSdkSha256 =
        "sha256:9025bd9ffd26a1f8a174cfdc71c0bbde6815b86101033bd3f669df5a484b6d95";
    private const string AspireSourceCommit =
        "87fe259e4fc244c599019a7b1304c85a1488f248";

    /// <inheritdoc />
    public AspireAppHostGenerationResult Generate(AspireAppHostDefinition definition)
    {
        ArgumentNullException.ThrowIfNull(definition);
        Validate(definition);

        var model = RenderModel(definition);
        var inputDigest = Hash(model.Span);
        var outputs = ImmutableArray.Create(
                Output("AppHost.csproj", RenderProject(definition)),
                Output("Program.cs", RenderProgram(definition)),
                Output("aspire-apphost.lock.json", RenderLock(definition, inputDigest)),
                new GeneratedOutput("apphost.model.json", model),
                Output("global.json", RenderGlobalJson()))
            .OrderBy(static output => output.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        return new AspireAppHostGenerationResult(outputs, HashTree(outputs));
    }

    private static void Validate(AspireAppHostDefinition definition)
    {
        if (definition.Integrations.IsDefault ||
            definition.Parameters.IsDefault ||
            definition.Resources.IsDefault ||
            definition.Endpoints.IsDefault ||
            definition.EnvironmentBindings.IsDefault ||
            definition.References.IsDefault ||
            definition.WaitDependencies.IsDefault ||
            definition.Volumes.IsDefault ||
            definition.Resources.IsEmpty)
        {
            throw Failure(
                DotNetDiagnosticIds.InvalidAspireComposition,
                "AppHost arrays must be initialized and at least one resource is required.",
                "/");
        }

        ValidateIntegrations(definition.Integrations);
        ValidateParameters(definition.Parameters);
        ValidateResources(definition.Resources);

        var resources = definition.Resources
            .ToDictionary(static resource => resource.Name, StringComparer.Ordinal);
        var parameters = definition.Parameters
            .ToDictionary(static parameter => parameter.Name, StringComparer.Ordinal);
        ValidateEndpoints(definition.Endpoints, resources);
        ValidateEnvironment(definition.EnvironmentBindings, resources, parameters);
        ValidateReferences(definition.References, resources, definition.Endpoints);
        ValidateWaits(definition.WaitDependencies, resources);
        ValidateVolumes(definition.Volumes, resources);
        ValidateAcyclic(definition.References, definition.WaitDependencies, resources.Keys);
    }

    private static void ValidateIntegrations(
        ImmutableArray<AspireIntegrationSelection> selections)
    {
        var distinct = selections
            .Select(static selection => Key(selection.Identity, selection.Version))
            .ToHashSet(StringComparer.Ordinal);
        if (distinct.Count != selections.Length)
        {
            throw Failure(
                DotNetDiagnosticIds.AspireIntegrationMismatch,
                "Aspire integration selections must be unique.",
                "/integrations");
        }

        var registered = AspireIntegrationCatalog.Descriptors
            .Select(static descriptor => Key(descriptor.Identity, descriptor.Version))
            .ToHashSet(StringComparer.Ordinal);
        var core = Key(
            AspireIntegrationCatalog.AppHost.Identity,
            AspireIntegrationCatalog.AppHost.Version);
        if (!distinct.Contains(core) || !distinct.IsSubsetOf(registered))
        {
            throw Failure(
                DotNetDiagnosticIds.AspireIntegrationMismatch,
                "The exact core AppHost integration is required and every selection must be registered.",
                "/integrations");
        }
    }

    private static void ValidateParameters(
        ImmutableArray<AspireParameterDefinition> parameters)
    {
        EnsureUnique(
            parameters.Select(static parameter => parameter.Name),
            "/parameters",
            "Parameter names must be unique.");
        foreach (var parameter in parameters)
        {
            if (!IsResourceName(parameter.Name) ||
                !IsConfigurationKey(parameter.ConfigurationKey))
            {
                throw Failure(
                    DotNetDiagnosticIds.InvalidAspireComposition,
                    "Parameter names and configuration keys must use the reviewed portable forms.",
                    "/parameters");
            }

            if (parameter.SecretReference is { } secret &&
                (secret.ExpectedResultKind !=
                    SecretResolution.Contracts.SecretResultKind.ConfigurationText ||
                 secret.Classification ==
                    SecretResolution.Contracts.SecretReferenceClassification.Unspecified ||
                 secret.LocatorClassification ==
                    SecretResolution.Contracts.SecretReferenceClassification.Unspecified))
            {
                throw Failure(
                    DotNetDiagnosticIds.UnsafeAspireSecretMaterial,
                    "Secret parameters require a classified reference resolving configuration text.",
                    "/parameters/secretReference");
            }
        }
    }

    private static void ValidateResources(
        ImmutableArray<AspireResourceDefinition> resources)
    {
        EnsureUnique(
            resources.Select(static resource => resource.Name),
            "/resources",
            "Resource names must be unique.");
        foreach (var resource in resources)
        {
            if (!IsResourceName(resource.Name) || resource.Arguments.IsDefault)
            {
                throw Failure(
                    DotNetDiagnosticIds.InvalidAspireComposition,
                    "Resources require a portable name and initialized arguments.",
                    "/resources");
            }

            var valid = resource.Kind switch
            {
                AspireResourceKind.Project =>
                    IsRelativePath(resource.ProjectPath, ".csproj") &&
                    IsCSharpIdentifier(resource.ProjectMetadataTypeName) &&
                    resource.ExecutablePath is null &&
                    resource.WorkingDirectory is null &&
                    resource.ContainerImage is null &&
                    resource.Arguments.IsEmpty,
                AspireResourceKind.Executable =>
                    IsRelativePath(resource.ExecutablePath) &&
                    IsRelativePath(resource.WorkingDirectory) &&
                    resource.ProjectPath is null &&
                    resource.ProjectMetadataTypeName is null &&
                    resource.ContainerImage is null &&
                    resource.Arguments.All(IsArgument),
                AspireResourceKind.Container =>
                    IsPinnedContainerImage(resource.ContainerImage) &&
                    resource.ProjectPath is null &&
                    resource.ProjectMetadataTypeName is null &&
                    resource.ExecutablePath is null &&
                    resource.WorkingDirectory is null &&
                    resource.Arguments.All(IsArgument),
                _ => false,
            };
            if (!valid)
            {
                throw Failure(
                    DotNetDiagnosticIds.InvalidAspireComposition,
                    "Each resource must populate exactly the fields allowed by its reviewed kind.",
                    "/resources");
            }
        }
    }

    private static void ValidateEndpoints(
        ImmutableArray<AspireEndpointDefinition> endpoints,
        Dictionary<string, AspireResourceDefinition> resources)
    {
        EnsureUnique(
            endpoints.Select(static endpoint =>
                string.Concat(endpoint.ResourceName, "|", endpoint.Name)),
            "/endpoints",
            "Endpoint names must be unique within each resource.");
        foreach (var endpoint in endpoints)
        {
            if (!resources.ContainsKey(endpoint.ResourceName) ||
                !IsResourceName(endpoint.Name) ||
                !IsScheme(endpoint.Scheme) ||
                endpoint.TargetPort is < 1 or > 65535 ||
                endpoint.HostPort is < 1 or > 65535)
            {
                throw RelationshipFailure(
                    "Endpoints require an existing resource, portable identity, scheme, and valid ports.",
                    "/endpoints");
            }
        }
    }

    private static void ValidateEnvironment(
        ImmutableArray<AspireEnvironmentBinding> bindings,
        Dictionary<string, AspireResourceDefinition> resources,
        Dictionary<string, AspireParameterDefinition> parameters)
    {
        EnsureUnique(
            bindings.Select(static binding =>
                string.Concat(binding.ResourceName, "|", binding.VariableName)),
            "/environmentBindings",
            "Environment variables must be unique within each resource.");
        foreach (var binding in bindings)
        {
            if (!resources.ContainsKey(binding.ResourceName) ||
                !parameters.ContainsKey(binding.ParameterName) ||
                !IsEnvironmentVariable(binding.VariableName))
            {
                throw RelationshipFailure(
                    "Environment bindings require an existing resource and parameter and a portable variable name.",
                    "/environmentBindings");
            }
        }
    }

    private static void ValidateReferences(
        ImmutableArray<AspireResourceReference> references,
        Dictionary<string, AspireResourceDefinition> resources,
        ImmutableArray<AspireEndpointDefinition> endpoints)
    {
        EnsureUnique(
            references.Select(static reference =>
                string.Concat(
                    reference.SourceResourceName,
                    "|",
                    reference.TargetResourceName,
                    "|",
                    reference.TargetEndpointName)),
            "/references",
            "Resource references must be unique.");
        var endpointKeys = endpoints
            .Select(static endpoint =>
                string.Concat(endpoint.ResourceName, "|", endpoint.Name))
            .ToHashSet(StringComparer.Ordinal);
        foreach (var reference in references)
        {
            if (!resources.ContainsKey(reference.SourceResourceName) ||
                !resources.ContainsKey(reference.TargetResourceName) ||
                reference.SourceResourceName == reference.TargetResourceName ||
                !endpointKeys.Contains(string.Concat(
                    reference.TargetResourceName,
                    "|",
                    reference.TargetEndpointName)))
            {
                throw RelationshipFailure(
                    "References require distinct existing resources and one exact declared target endpoint.",
                    "/references");
            }
        }
    }

    private static void ValidateWaits(
        ImmutableArray<AspireWaitDependency> waits,
        Dictionary<string, AspireResourceDefinition> resources)
    {
        EnsureUnique(
            waits.Select(static wait =>
                string.Concat(wait.SourceResourceName, "|", wait.TargetResourceName)),
            "/waitDependencies",
            "Wait dependencies must be unique.");
        foreach (var wait in waits)
        {
            if (!resources.ContainsKey(wait.SourceResourceName) ||
                !resources.ContainsKey(wait.TargetResourceName) ||
                wait.SourceResourceName == wait.TargetResourceName)
            {
                throw RelationshipFailure(
                    "Wait dependencies require two distinct existing resources.",
                    "/waitDependencies");
            }
        }
    }

    private static void ValidateVolumes(
        ImmutableArray<AspireVolumeDefinition> volumes,
        Dictionary<string, AspireResourceDefinition> resources)
    {
        EnsureUnique(
            volumes.Select(static volume =>
                string.Concat(volume.ResourceName, "|", volume.Name)),
            "/volumes",
            "Volume names must be unique within each resource.");
        foreach (var volume in volumes)
        {
            if (!resources.TryGetValue(volume.ResourceName, out var resource) ||
                resource.Kind != AspireResourceKind.Container ||
                !IsResourceName(volume.Name) ||
                !IsContainerPath(volume.TargetPath))
            {
                throw RelationshipFailure(
                    "Named volumes require an existing container, portable name, and absolute container target path.",
                    "/volumes");
            }
        }
    }

    private static void ValidateAcyclic(
        ImmutableArray<AspireResourceReference> references,
        ImmutableArray<AspireWaitDependency> waits,
        IEnumerable<string> resourceNames)
    {
        var adjacency = resourceNames.ToDictionary(
            static name => name,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        foreach (var reference in references)
        {
            adjacency[reference.SourceResourceName].Add(reference.TargetResourceName);
        }

        foreach (var wait in waits)
        {
            adjacency[wait.SourceResourceName].Add(wait.TargetResourceName);
        }

        var visiting = new HashSet<string>(StringComparer.Ordinal);
        var visited = new HashSet<string>(StringComparer.Ordinal);
        foreach (var resource in adjacency.Keys.Order(StringComparer.Ordinal))
        {
            if (HasCycle(resource, adjacency, visiting, visited))
            {
                throw RelationshipFailure(
                    "Aspire resource reference and wait relationships must be acyclic.",
                    "/references");
            }
        }
    }

    private static bool HasCycle(
        string resource,
        Dictionary<string, HashSet<string>> adjacency,
        HashSet<string> visiting,
        HashSet<string> visited)
    {
        if (visited.Contains(resource))
        {
            return false;
        }

        if (!visiting.Add(resource))
        {
            return true;
        }

        foreach (var dependency in adjacency[resource].Order(StringComparer.Ordinal))
        {
            if (HasCycle(dependency, adjacency, visiting, visited))
            {
                return true;
            }
        }

        visiting.Remove(resource);
        visited.Add(resource);
        return false;
    }

    private static string RenderProject(AspireAppHostDefinition definition)
    {
        var builder = new StringBuilder();
        builder.Append("<Project Sdk=\"Aspire.AppHost.Sdk/")
            .Append(AspireVersion)
            .AppendLine("\">");
        builder.AppendLine("  <PropertyGroup>");
        builder.AppendLine("    <OutputType>Exe</OutputType>");
        builder.Append("    <TargetFramework>").Append(TargetFramework).AppendLine("</TargetFramework>");
        builder.AppendLine("    <Nullable>enable</Nullable>");
        builder.AppendLine("    <ImplicitUsings>enable</ImplicitUsings>");
        builder.AppendLine("    <LangVersion>14.0</LangVersion>");
        builder.AppendLine("    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>");
        builder.AppendLine("    <EnableNETAnalyzers>true</EnableNETAnalyzers>");
        builder.AppendLine("    <AnalysisLevel>latest-all</AnalysisLevel>");
        builder.AppendLine("  </PropertyGroup>");
        builder.AppendLine("  <ItemGroup>");
        foreach (var descriptor in ResolveIntegrations(definition.Integrations))
        {
            builder.Append("    <PackageReference Include=\"")
                .Append(DotNetSourceText.Xml(descriptor.PackageName))
                .Append("\" Version=\"[")
                .Append(DotNetSourceText.Xml(descriptor.PackageVersion.Value))
                .AppendLine("]\" />");
        }

        builder.AppendLine("  </ItemGroup>");
        var projects = definition.Resources
            .Where(static resource => resource.Kind == AspireResourceKind.Project)
            .OrderBy(static resource => resource.Name, StringComparer.Ordinal)
            .ToArray();
        if (projects.Length > 0)
        {
            builder.AppendLine("  <ItemGroup>");
            foreach (var project in projects)
            {
                builder.Append("    <ProjectReference Include=\"")
                    .Append(DotNetSourceText.Xml(project.ProjectPath!))
                    .Append("\" AspireProjectMetadataTypeName=\"")
                    .Append(DotNetSourceText.Xml(project.ProjectMetadataTypeName!))
                    .AppendLine("\" />");
            }

            builder.AppendLine("  </ItemGroup>");
        }

        builder.AppendLine("</Project>");
        return builder.ToString();
    }

    private static string RenderProgram(AspireAppHostDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("var builder = global::Aspire.Hosting.DistributedApplication.CreateBuilder(args);");
        builder.AppendLine();
        foreach (var parameter in definition.Parameters.OrderBy(
                     static parameter => parameter.Name,
                     StringComparer.Ordinal))
        {
            builder.Append("var ").Append(ParameterVariable(parameter.Name))
                .Append(" = global::Aspire.Hosting.ParameterResourceBuilderExtensions.AddParameterFromConfiguration(")
                .AppendLine();
            builder.AppendLine("    builder,");
            builder.Append("    ").Append(DotNetSourceText.CSharpLiteral(parameter.Name)).AppendLine(",");
            builder.Append("    ").Append(DotNetSourceText.CSharpLiteral(parameter.ConfigurationKey)).AppendLine(",");
            builder.Append("    secret: ")
                .Append(parameter.SecretReference is null ? "false" : "true")
                .AppendLine(");");
        }

        if (!definition.Parameters.IsEmpty)
        {
            builder.AppendLine();
        }

        foreach (var resource in definition.Resources.OrderBy(
                     static resource => resource.Name,
                     StringComparer.Ordinal))
        {
            RenderResource(builder, resource);
        }

        foreach (var endpoint in definition.Endpoints
                     .OrderBy(static endpoint => endpoint.ResourceName, StringComparer.Ordinal)
                     .ThenBy(static endpoint => endpoint.Name, StringComparer.Ordinal))
        {
            builder.Append(ResourceVariable(endpoint.ResourceName)).AppendLine(".WithEndpoint(");
            builder.Append("    port: ")
                .Append(endpoint.HostPort?.ToString(CultureInfo.InvariantCulture) ?? "null")
                .AppendLine(",");
            builder.Append("    targetPort: ")
                .Append(endpoint.TargetPort.ToString(CultureInfo.InvariantCulture))
                .AppendLine(",");
            builder.Append("    name: ").Append(DotNetSourceText.CSharpLiteral(endpoint.Name)).AppendLine(",");
            builder.Append("    scheme: ").Append(DotNetSourceText.CSharpLiteral(endpoint.Scheme)).AppendLine(",");
            builder.Append("    isExternal: ").Append(Boolean(endpoint.IsExternal)).AppendLine(",");
            builder.Append("    isProxied: ").Append(Boolean(endpoint.IsProxied)).AppendLine(");");
        }

        foreach (var volume in definition.Volumes
                     .OrderBy(static volume => volume.ResourceName, StringComparer.Ordinal)
                     .ThenBy(static volume => volume.Name, StringComparer.Ordinal))
        {
            builder.Append(ResourceVariable(volume.ResourceName)).Append(".WithVolume(")
                .Append(DotNetSourceText.CSharpLiteral(volume.Name)).Append(", ")
                .Append(DotNetSourceText.CSharpLiteral(volume.TargetPath))
                .Append(", isReadOnly: ").Append(Boolean(volume.IsReadOnly)).AppendLine(");");
        }

        foreach (var binding in definition.EnvironmentBindings
                     .OrderBy(static binding => binding.ResourceName, StringComparer.Ordinal)
                     .ThenBy(static binding => binding.VariableName, StringComparer.Ordinal))
        {
            builder.Append(ResourceVariable(binding.ResourceName)).Append(".WithEnvironment(")
                .Append(DotNetSourceText.CSharpLiteral(binding.VariableName)).Append(", ")
                .Append(ParameterVariable(binding.ParameterName)).AppendLine(");");
        }

        foreach (var reference in definition.References
                     .OrderBy(static reference => reference.SourceResourceName, StringComparer.Ordinal)
                     .ThenBy(static reference => reference.TargetResourceName, StringComparer.Ordinal))
        {
            builder.Append(ResourceVariable(reference.SourceResourceName)).Append(".WithReference(")
                .Append(ResourceVariable(reference.TargetResourceName))
                .Append(".GetEndpoint(")
                .Append(DotNetSourceText.CSharpLiteral(reference.TargetEndpointName))
                .AppendLine("));");
        }

        foreach (var wait in definition.WaitDependencies
                     .OrderBy(static wait => wait.SourceResourceName, StringComparer.Ordinal)
                     .ThenBy(static wait => wait.TargetResourceName, StringComparer.Ordinal))
        {
            builder.Append(ResourceVariable(wait.SourceResourceName)).Append(".WaitFor(")
                .Append(ResourceVariable(wait.TargetResourceName)).AppendLine(");");
        }

        builder.AppendLine();
        builder.AppendLine("builder.Build().Run();");
        return builder.ToString();
    }

    private static void RenderResource(StringBuilder builder, AspireResourceDefinition resource)
    {
        builder.Append("var ").Append(ResourceVariable(resource.Name)).Append(" = ");
        switch (resource.Kind)
        {
            case AspireResourceKind.Project:
                builder.Append("builder.AddProject<global::Projects.")
                    .Append(resource.ProjectMetadataTypeName)
                    .Append(">(")
                    .Append(DotNetSourceText.CSharpLiteral(resource.Name))
                    .AppendLine(");");
                break;
            case AspireResourceKind.Executable:
                builder.Append("builder.AddExecutable(")
                    .Append(DotNetSourceText.CSharpLiteral(resource.Name)).Append(", ")
                    .Append(DotNetSourceText.CSharpLiteral(resource.ExecutablePath!)).Append(", ")
                    .Append(DotNetSourceText.CSharpLiteral(resource.WorkingDirectory!)).Append(", ");
                RenderArguments(builder, resource.Arguments);
                builder.AppendLine(");");
                break;
            case AspireResourceKind.Container:
                builder.Append("builder.AddContainer(")
                    .Append(DotNetSourceText.CSharpLiteral(resource.Name)).Append(", ")
                    .Append(DotNetSourceText.CSharpLiteral(resource.ContainerImage!))
                    .Append(')');
                foreach (var argument in resource.Arguments)
                {
                    builder.AppendLine();
                    builder.Append("    .WithArgs(")
                        .Append(DotNetSourceText.CSharpLiteral(argument))
                        .Append(')');
                }

                builder.AppendLine(";");
                break;
            default:
                throw Failure(
                    DotNetDiagnosticIds.AspireGenerationFailed,
                    "An unsupported resource reached rendering.",
                    "/resources");
        }
    }

    private static void RenderArguments(
        StringBuilder builder,
        ImmutableArray<string> arguments)
    {
        builder.Append('[');
        for (var index = 0; index < arguments.Length; index++)
        {
            if (index > 0)
            {
                builder.Append(", ");
            }

            builder.Append(DotNetSourceText.CSharpLiteral(arguments[index]));
        }

        builder.Append(']');
    }

    private static ReadOnlyMemory<byte> RenderModel(AspireAppHostDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.Append("  \"identity\": ").Append(DotNetSourceText.JsonLiteral(definition.Identity.Value)).AppendLine(",");
        builder.Append("  \"version\": ").Append(DotNetSourceText.JsonLiteral(definition.Version.Value)).AppendLine(",");
        builder.AppendLine("  \"resources\": [");
        WriteModelResources(builder, definition.Resources);
        builder.AppendLine("  ],");
        builder.AppendLine("  \"parameters\": [");
        WriteModelParameters(builder, definition.Parameters);
        builder.AppendLine("  ],");
        WriteRelationships(builder, "endpoints", definition.Endpoints.Select(static endpoint =>
            string.Concat(endpoint.ResourceName, "|", endpoint.Name, "|", endpoint.Scheme, "|",
                endpoint.TargetPort.ToString(CultureInfo.InvariantCulture), "|",
                endpoint.HostPort?.ToString(CultureInfo.InvariantCulture) ?? string.Empty, "|",
                Boolean(endpoint.IsExternal), "|", Boolean(endpoint.IsProxied))));
        builder.AppendLine(",");
        WriteRelationships(builder, "environmentBindings", definition.EnvironmentBindings.Select(static binding =>
            string.Concat(binding.ResourceName, "|", binding.VariableName, "|", binding.ParameterName)));
        builder.AppendLine(",");
        WriteRelationships(builder, "references", definition.References.Select(static reference =>
            string.Concat(
                reference.SourceResourceName,
                "|",
                reference.TargetResourceName,
                "|",
                reference.TargetEndpointName)));
        builder.AppendLine(",");
        WriteRelationships(builder, "waitDependencies", definition.WaitDependencies.Select(static wait =>
            string.Concat(wait.SourceResourceName, "|", wait.TargetResourceName)));
        builder.AppendLine(",");
        WriteRelationships(builder, "volumes", definition.Volumes.Select(static volume =>
            string.Concat(volume.ResourceName, "|", volume.Name, "|", volume.TargetPath, "|",
                Boolean(volume.IsReadOnly))));
        builder.AppendLine();
        builder.AppendLine("}");
        return DotNetSourceText.Utf8(builder.ToString());
    }

    private static void WriteModelResources(
        StringBuilder builder,
        ImmutableArray<AspireResourceDefinition> resources)
    {
        var ordered = resources.OrderBy(static item => item.Name, StringComparer.Ordinal).ToArray();
        for (var index = 0; index < ordered.Length; index++)
        {
            var item = ordered[index];
            builder.Append("    { \"name\": ").Append(DotNetSourceText.JsonLiteral(item.Name))
                .Append(", \"kind\": ")
                .Append(DotNetSourceText.JsonLiteral(item.Kind.ToString().ToLowerInvariant()))
                .Append(" }")
                .AppendLine(index == ordered.Length - 1 ? string.Empty : ",");
        }
    }

    private static void WriteModelParameters(
        StringBuilder builder,
        ImmutableArray<AspireParameterDefinition> parameters)
    {
        var ordered = parameters.OrderBy(static item => item.Name, StringComparer.Ordinal).ToArray();
        for (var index = 0; index < ordered.Length; index++)
        {
            var item = ordered[index];
            builder.Append("    { \"name\": ").Append(DotNetSourceText.JsonLiteral(item.Name))
                .Append(", \"configurationKey\": ")
                .Append(DotNetSourceText.JsonLiteral(item.ConfigurationKey))
                .Append(", \"secret\": ").Append(Boolean(item.SecretReference is not null));
            if (item.SecretReference is { } secret)
            {
                builder.Append(", \"referenceSha256\": ")
                    .Append(DotNetSourceText.JsonLiteral(HashText(secret.Identity.Value).Value))
                    .Append(", \"referenceClassification\": ")
                    .Append(DotNetSourceText.JsonLiteral(
                        secret.Classification.ToString().ToLowerInvariant()))
                    .Append(", \"locatorClassification\": ")
                    .Append(DotNetSourceText.JsonLiteral(
                        secret.LocatorClassification.ToString().ToLowerInvariant()));
            }

            builder.Append(" }").AppendLine(index == ordered.Length - 1 ? string.Empty : ",");
        }
    }

    private static void WriteRelationships(
        StringBuilder builder,
        string name,
        IEnumerable<string> values)
    {
        builder.Append("  ").Append(DotNetSourceText.JsonLiteral(name)).AppendLine(": [");
        var ordered = values.Order(StringComparer.Ordinal).ToArray();
        for (var index = 0; index < ordered.Length; index++)
        {
            builder.Append("    ").Append(DotNetSourceText.JsonLiteral(ordered[index]))
                .AppendLine(index == ordered.Length - 1 ? string.Empty : ",");
        }

        builder.Append("  ]");
    }

    private static string RenderLock(
        AspireAppHostDefinition definition,
        Sha256Digest inputDigest)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"lockVersion\": \"1.0.0\",");
        builder.Append("  \"inputSha256\": ").Append(DotNetSourceText.JsonLiteral(inputDigest.Value)).AppendLine(",");
        builder.Append("  \"dotnetSdk\": ").Append(DotNetSourceText.JsonLiteral(DotNetSdkVersion)).AppendLine(",");
        builder.Append("  \"targetFramework\": ").Append(DotNetSourceText.JsonLiteral(TargetFramework)).AppendLine(",");
        builder.AppendLine("  \"aspireSdk\": {");
        builder.AppendLine("    \"package\": \"Aspire.AppHost.Sdk\",");
        builder.Append("    \"version\": ").Append(DotNetSourceText.JsonLiteral(AspireVersion)).AppendLine(",");
        builder.Append("    \"packageSha256\": ").Append(DotNetSourceText.JsonLiteral(AspireSdkSha256)).AppendLine(",");
        builder.Append("    \"sourceCommit\": ").Append(DotNetSourceText.JsonLiteral(AspireSourceCommit)).AppendLine();
        builder.AppendLine("  },");
        builder.AppendLine("  \"integrations\": [");
        var integrations = ResolveIntegrations(definition.Integrations);
        for (var index = 0; index < integrations.Length; index++)
        {
            var item = integrations[index];
            builder.Append("    { \"identity\": ").Append(DotNetSourceText.JsonLiteral(item.Identity.Value))
                .Append(", \"version\": ").Append(DotNetSourceText.JsonLiteral(item.Version.Value))
                .Append(", \"package\": ").Append(DotNetSourceText.JsonLiteral(item.PackageName))
                .Append(", \"packageVersion\": ").Append(DotNetSourceText.JsonLiteral(item.PackageVersion.Value))
                .Append(", \"packageSha256\": ").Append(DotNetSourceText.JsonLiteral(item.PackageSha256.Value))
                .Append(" }").AppendLine(index == integrations.Length - 1 ? string.Empty : ",");
        }

        builder.AppendLine("  ],");
        builder.AppendLine("  \"platformSpecificRestore\": {");
        builder.AppendLine("    \"state\": \"deferred-to-separate-human-started-restore\",");
        builder.AppendLine("    \"reason\": \"Aspire injects dashboard and orchestration packages for the build SDK runtime identifier\"");
        builder.AppendLine("  },");
        builder.AppendLine("  \"executionAuthorized\": false,");
        builder.AppendLine("  \"deploymentMeaning\": false");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderGlobalJson() =>
        string.Concat(
            "{\n",
            "  \"sdk\": {\n",
            "    \"version\": \"", DotNetSdkVersion, "\",\n",
            "    \"rollForward\": \"disable\",\n",
            "    \"allowPrerelease\": false\n",
            "  }\n",
            "}\n");

    private static ImmutableArray<AspireIntegrationDescriptor> ResolveIntegrations(
        ImmutableArray<AspireIntegrationSelection> selections) =>
        selections
            .Select(selection => AspireIntegrationCatalog.Descriptors.Single(
                descriptor =>
                    descriptor.Identity == selection.Identity &&
                    descriptor.Version == selection.Version))
            .OrderBy(static descriptor => descriptor.Identity.Value, StringComparer.Ordinal)
            .ToImmutableArray();

    private static GeneratedOutput Output(string path, string text) =>
        new(path, DotNetSourceText.Utf8(text));

    private static Sha256Digest Hash(ReadOnlySpan<byte> bytes) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(bytes))));

    private static Sha256Digest HashText(string value) =>
        Hash(Encoding.UTF8.GetBytes(value));

    private static Sha256Digest HashTree(ImmutableArray<GeneratedOutput> outputs)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var output in outputs.OrderBy(
                     static output => output.RelativePath,
                     StringComparer.Ordinal))
        {
            hash.AppendData(Encoding.UTF8.GetBytes(output.RelativePath));
            hash.AppendData([0]);
            hash.AppendData(output.Content.Span);
            hash.AppendData([0]);
        }

        return new Sha256Digest(
            string.Concat("sha256:", Convert.ToHexStringLower(hash.GetHashAndReset())));
    }

    private static void EnsureUnique(
        IEnumerable<string> values,
        string path,
        string message)
    {
        var array = values.ToArray();
        if (array.Distinct(StringComparer.Ordinal).Count() != array.Length)
        {
            throw RelationshipFailure(message, path);
        }
    }

    private static bool IsResourceName(string? value) =>
        value is { Length: >= 1 and <= 63 } &&
        value[0] is >= 'a' and <= 'z' &&
        value.All(static character =>
            character is >= 'a' and <= 'z' or >= '0' and <= '9' or '-');

    private static bool IsCSharpIdentifier(string? value)
    {
        if (string.IsNullOrEmpty(value) ||
            !(char.IsLetter(value[0]) || value[0] == '_'))
        {
            return false;
        }

        return value.Skip(1).All(static character =>
            char.IsLetterOrDigit(character) || character == '_');
    }

    private static bool IsRelativePath(string? value, string? requiredSuffix = null) =>
        !string.IsNullOrWhiteSpace(value) &&
        !Path.IsPathRooted(value) &&
        !value.Contains('\\') &&
        !value.Contains('\0') &&
        (requiredSuffix is null ||
         value.EndsWith(requiredSuffix, StringComparison.OrdinalIgnoreCase));

    private static bool IsPinnedContainerImage(string? value)
    {
        const string separator = "@sha256:";
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var index = value.LastIndexOf(separator, StringComparison.Ordinal);
        if (index < 1 || index + separator.Length + 64 != value.Length)
        {
            return false;
        }

        return value[(index + separator.Length)..].All(static character =>
            character is >= '0' and <= '9' or >= 'a' and <= 'f');
    }

    private static bool IsArgument(string value) =>
        value.Length <= 1024 &&
        !value.Contains('\0') &&
        !value.Contains('\r') &&
        !value.Contains('\n');

    private static bool IsScheme(string value) =>
        value is "http" or "https" or "tcp" or "udp";

    private static bool IsConfigurationKey(string value) =>
        value is { Length: >= 1 and <= 256 } &&
        !value.StartsWith(':') &&
        !value.EndsWith(':') &&
        !value.Contains("::", StringComparison.Ordinal) &&
        value.All(static character =>
            char.IsLetterOrDigit(character) || character is ':' or '-' or '_' or '.');

    private static bool IsEnvironmentVariable(string value) =>
        value is { Length: >= 1 and <= 128 } &&
        value[0] is >= 'A' and <= 'Z' or '_' &&
        value.All(static character =>
            character is >= 'A' and <= 'Z' or >= '0' and <= '9' or '_');

    private static bool IsContainerPath(string value) =>
        value.StartsWith('/') &&
        !value.Contains("..", StringComparison.Ordinal) &&
        !value.Contains('\\') &&
        !value.Contains('\0');

    private static string Key(ProgramKitIdentifier identity, SemanticVersion version) =>
        string.Concat(identity.Value, "@", version.Value);

    private static string ResourceVariable(string name) =>
        string.Concat("resource", HashSuffix(name));

    private static string ParameterVariable(string name) =>
        string.Concat("parameter", HashSuffix(name));

    private static string HashSuffix(string value) =>
        Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(value)))[..12];

    private static string Boolean(bool value) => value ? "true" : "false";

    private static DotNetKitException RelationshipFailure(string message, string path) =>
        Failure(DotNetDiagnosticIds.InvalidAspireRelationship, message, path);

    private static DotNetKitException Failure(
        string diagnosticId,
        string message,
        string path) =>
        DotNetKitException.Create(diagnosticId, message, path);
}
