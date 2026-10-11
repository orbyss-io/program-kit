using System.Collections;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using ProgramKit.Foundation.TestSupport;

namespace ProgramKit.Qualification;

/// <summary>Observes existing owner options and immutable provider policy; never rebinds input.</summary>
public static class RuntimeOptionsObservation
{
    /// <summary>Captures activated owners and explicitly reports unavailable native observations.</summary>
    public static IReadOnlyList<object> Capture(IServiceProvider services, IConfigurationRoot configuration, JsonElement scopes)
    {
        var results = new List<object>();
        foreach (var group in scopes.EnumerateArray().GroupBy(scope => scope.GetProperty("owner").GetString()))
        {
            var owner = group.Key!;
            try
            {
            if (owner is "Orbyss.Foundation.Authentication" or "Orbyss.Foundation.Authentication.BffCookie") continue;
            var settings = group.SelectMany(scope => scope.GetProperty("settings").EnumerateArray()).ToArray();
            foreach (var (section, typeName) in owner switch
            {
                "Orbyss.Foundation.WebDefaults" => new[] {
                    ("Foundation:Web", "Orbyss.Foundation.WebDefaults.FoundationWebDefaultsOptions"),
                    ("Foundation:Web:ResponsePolicies", "Orbyss.Foundation.WebDefaults.WebResponsePoliciesOptions") },
                "Orbyss.Foundation.Json.AspNetCore" => [("Foundation:Json", "Orbyss.Foundation.Json.AspNetCore.FoundationJsonOptions")],
                _ => Array.Empty<(string,string)>()
            })
            {
                var candidates=AppDomain.CurrentDomain.GetAssemblies().Where(value => value.GetName().Name==owner)
                    .Where(assembly => OwnerCatalogType(assembly,owner) is { } catalogType && services.GetService(catalogType) is not null)
                    .Where(assembly => HasConfiguredOptions(services,assembly.GetType(typeName,throwOnError:true)!)).ToArray();
                if (candidates.Length==0)
                {
                    results.Add(new {owner,section,observationStatus="owner-catalog-not-activated",
                        reason="No actual registered compiled owner catalog exists in this shell; typed defaults are not substituted for activated options."});
                    continue;
                }
                if (candidates.Length!=1) throw new InvalidOperationException("Ambiguous actual registered owner catalogs.");
                var assembly=candidates[0];
                var type = assembly.GetType(typeName, throwOnError:true)!;
                var serviceType = typeof(IOptions<>).MakeGenericType(type);
                var options = services.GetRequiredService(serviceType);
                var activated = serviceType.GetProperty("Value")!.GetValue(options)!;
                var relevant = settings.Where(setting => setting.GetProperty("path").GetString()!.StartsWith(section+":", StringComparison.Ordinal));
                if (section == "Foundation:Web") relevant = relevant.Where(setting => !setting.GetProperty("path").GetString()!.StartsWith("Foundation:Web:ResponsePolicies:", StringComparison.Ordinal));
                var expanded = relevant.SelectMany(setting => Expand(setting, activated, section)).ToArray();
                results.Add(new {owner, section, observationStatus="activated", runtimeType=type.FullName,
                    assemblyVersion=assembly.GetName().Version?.ToString(),assemblyPath=assembly.Location,
                    assemblySha256=Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(assembly.Location))),
                    settings=EffectiveSettings.Capture(configuration,activated,section,expanded)});
            }
            if (owner == "Orbyss.Foundation.PostgreSql")
            {
                var assemblies=AppDomain.CurrentDomain.GetAssemblies().Where(value => value.GetName().Name==owner)
                    .Where(assembly => assembly.GetType("Orbyss.Foundation.PostgreSql.PostgreSqlPolicy") is { } policyType &&
                        services.GetKeyedService(policyType,"application") is not null).ToArray();
                if (assemblies.Length!=1) throw new InvalidOperationException("Selected native keyed provider policy is absent or ambiguous.");
                var assembly=assemblies[0];
                var type=assembly.GetType("Orbyss.Foundation.PostgreSql.PostgreSqlPolicy",throwOnError:true)!;
                var policy=services.GetRequiredKeyedService(type,"application");
                var values=new Dictionary<string,object?>();
                var available=new List<JsonElement>();
                foreach (var setting in settings)
                {
                    var node=JsonNode.Parse(setting.GetRawText())!;
                    node["path"]=setting.GetProperty("path").GetString()!.Replace("{policyName}","application",StringComparison.Ordinal);
                    var property=node["path"]!.GetValue<string>().Split(':')[^1];
                    if (property=="CancellationTimeout")
                    {
                        results.Add(new {owner, path=node["path"]!.GetValue<string>(),observationStatus="native-normalization-not-observed",
                            reason="Npgsql datasource normalizes this setting without retaining an accessible policy property; native provider qualification remains required."});
                        continue;
                    }
                    values[property]=setting.GetProperty("secret").GetBoolean() ? "<redacted>" :
                        type.GetProperty(property,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)!.GetValue(policy);
                    available.Add(JsonSerializer.SerializeToElement(node));
                }
                results.Add(new {owner,section="Foundation:PostgreSql:Policies:application",observationStatus="activated immutable keyed policy",
                    assemblyVersion=assembly.GetName().Version?.ToString(),assemblyPath=assembly.Location,
                    assemblySha256=Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(assembly.Location))),
                    runtimeType=type.FullName,settings=EffectiveSettings.Capture(configuration,values,"Foundation:PostgreSql:Policies:application",available)});
            }
            if (owner == "Orbyss.Foundation.Web.ProblemDetails")
                results.Add(new {owner,observationStatus="source-contract-only",reason="Problem response options are application code registrations, rather than a named shell configuration section."});
            }
            catch (Exception error)
            {
                error.Data["ProgramKitObservationOwner"]=owner;
                throw;
            }
        }
        return results;
    }

    /// <summary>Observes the authentication instance with actual typed feature registrations.</summary>
    public static (IReadOnlyList<SettingObservation> Settings, object Assembly, object ProfileAssembly) CaptureAuthentication(IServiceProvider services, IConfigurationRoot configuration,
        IEnumerable<JsonElement> settings)
    {
        const string owner="Orbyss.Foundation.Authentication";
        const string typeName="Orbyss.Foundation.Authentication.FoundationWebOptions";
        var candidates=AppDomain.CurrentDomain.GetAssemblies().Where(value => value.GetName().Name==owner)
            .Where(assembly => assembly.GetType("Orbyss.Foundation.Authentication.IValidatedAccountIdentityReader") is { } reader &&
                services.GetService(reader) is not null && HasConfiguredOptions(services,assembly.GetType(typeName,throwOnError:true)!)).ToArray();
        if (candidates.Length!=1) throw new InvalidOperationException("Actual configured authentication owner is absent or ambiguous.");
        var serviceType=typeof(IOptions<>).MakeGenericType(candidates[0].GetType(typeName,throwOnError:true)!);
        var options=services.GetRequiredService(serviceType);
        var assembly=candidates[0];
        var profileType=assembly.GetType("Orbyss.Foundation.Authentication.IFoundationAuthenticationProfile",throwOnError:true)!;
        var profiles=services.GetServices(profileType).Where(profile => profile?.GetType().Assembly.GetName().Name=="Orbyss.Foundation.Authentication.BffCookie").ToArray();
        if (profiles.Length!=1) throw new InvalidOperationException("Actual BFF profile owner is absent or ambiguous.");
        var profileAssembly=profiles[0]!.GetType().Assembly;
        return (EffectiveSettings.Capture(configuration,serviceType.GetProperty("Value")!.GetValue(options)!,"Foundation:Web",settings),
            new {owner,assemblyVersion=assembly.GetName().Version?.ToString(),assemblyPath=assembly.Location,
                assemblySha256=Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(assembly.Location)))},
            new {owner="Orbyss.Foundation.Authentication.BffCookie",assemblyVersion=profileAssembly.GetName().Version?.ToString(),assemblyPath=profileAssembly.Location,
                assemblySha256=Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(profileAssembly.Location)))});
    }

    /// <summary>Requires feature-owned binding delegates, avoiding open-generic options defaults for inactive types.</summary>
    private static bool HasConfiguredOptions(IServiceProvider services,Type type) =>
        services.GetServices(typeof(IConfigureOptions<>).MakeGenericType(type)).Any();

    /// <summary>Instantiates named metadata from actual options dictionary keys, without rebinding.</summary>
    private static IEnumerable<JsonElement> Expand(JsonElement setting, object activated, string section)
    {
        var path=setting.GetProperty("path").GetString()!;
        if (!path.Contains('{',StringComparison.Ordinal)) { yield return setting; yield break; }
        var relative=path[(section.Length+1)..].Split(':');
        var dictionary=activated.GetType().GetProperty(relative[0])!.GetValue(activated) as IDictionary
            ?? throw new InvalidOperationException("Named metadata does not bind an actual options dictionary.");
        foreach (string key in dictionary.Keys)
        {
            var node=JsonNode.Parse(setting.GetRawText())!;
            node["path"]=path.Replace(relative[1],key,StringComparison.Ordinal);
            yield return JsonSerializer.SerializeToElement(node);
        }
    }

    /// <summary>Finds the catalog type through the selected owner's actual assembly dependency context.</summary>
    private static Type? OwnerCatalogType(Assembly assembly,string owner)
    {
        if (owner=="Orbyss.Foundation.WebDefaults") return assembly.GetType("Orbyss.Foundation.WebDefaults.WebResponsePolicyCatalog");
        var dependency=System.Runtime.Loader.AssemblyLoadContext.GetLoadContext(assembly)!.LoadFromAssemblyName(new AssemblyName("Orbyss.Foundation.Json"));
        return dependency.GetType("Orbyss.Foundation.Json.JsonProfileCatalog");
    }
}
