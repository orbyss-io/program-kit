using System.Collections;
using System.Globalization;
using System.Reflection;
using System.Text.Json;

namespace Orbyss.ProgramKit.Workbench.Operations.Schemas;

internal sealed class JsonSchemaNetReflection
{
    private readonly Type schemaType;
    private readonly Type buildOptionsType;
    private readonly object buildOptions;
    private readonly object schemaRegistry;
    private readonly MethodInfo fromText;
    private readonly MethodInfo registryRegister;
    private readonly MethodInfo evaluate;
    private readonly Type evaluationOptionsType;
    private readonly object listOutputFormat;
    private readonly Dictionary<string, object> schemas = new(StringComparer.Ordinal);

    private JsonSchemaNetReflection(
        Type schemaType,
        Type buildOptionsType,
        object buildOptions,
        object schemaRegistry,
        MethodInfo fromText,
        MethodInfo registryRegister,
        MethodInfo evaluate,
        Type evaluationOptionsType,
        object listOutputFormat)
    {
        this.schemaType = schemaType;
        this.buildOptionsType = buildOptionsType;
        this.buildOptions = buildOptions;
        this.schemaRegistry = schemaRegistry;
        this.fromText = fromText;
        this.registryRegister = registryRegister;
        this.evaluate = evaluate;
        this.evaluationOptionsType = evaluationOptionsType;
        this.listOutputFormat = listOutputFormat;
    }

    internal static JsonSchemaNetReflection Create()
    {
        var assembly = Assembly.Load("JsonSchema.Net");
        var schemaType = RequireType(assembly, "Json.Schema.JsonSchema");
        var buildOptionsType = RequireType(assembly, "Json.Schema.BuildOptions");
        var registryType = RequireType(assembly, "Json.Schema.SchemaRegistry");
        var evaluationOptionsType = RequireType(assembly, "Json.Schema.EvaluationOptions");
        var outputFormatType = RequireType(assembly, "Json.Schema.OutputFormat");
        var buildOptions = Activator.CreateInstance(buildOptionsType) ??
            throw new InvalidOperationException("JsonSchema.Net BuildOptions could not be created.");
        var schemaRegistry = Activator.CreateInstance(registryType) ??
            throw new InvalidOperationException("JsonSchema.Net SchemaRegistry could not be created.");
        RequireProperty(buildOptionsType, "SchemaRegistry").SetValue(buildOptions, schemaRegistry);

        var fromText = schemaType.GetMethods(BindingFlags.Public | BindingFlags.Static)
            .Single(method =>
                string.Equals(method.Name, "FromText", StringComparison.Ordinal) &&
                method.GetParameters().Length == 4);
        var registryRegister = registryType.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Single(method =>
                string.Equals(method.Name, "Register", StringComparison.Ordinal) &&
                method.GetParameters().Length == 2 &&
                method.GetParameters()[0].ParameterType == typeof(Uri));
        var evaluate = schemaType.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Single(method =>
                string.Equals(method.Name, "Evaluate", StringComparison.Ordinal) &&
                method.GetParameters().Length == 2 &&
                method.GetParameters()[0].ParameterType == typeof(JsonElement));
        var listOutputFormat = Enum.Parse(outputFormatType, "List", ignoreCase: false);
        return new JsonSchemaNetReflection(
            schemaType,
            buildOptionsType,
            buildOptions,
            schemaRegistry,
            fromText,
            registryRegister,
            evaluate,
            evaluationOptionsType,
            listOutputFormat);
    }

    internal void Register(Uri uri, string schemaText)
    {
        ArgumentNullException.ThrowIfNull(uri);
        ArgumentNullException.ThrowIfNull(schemaText);
        var schema = fromText.Invoke(
            null,
            [schemaText, buildOptions, uri, null]) ??
            throw new InvalidOperationException("JsonSchema.Net did not build a schema.");
        registryRegister.Invoke(schemaRegistry, [uri, schema]);
        schemas.Add(uri.AbsoluteUri, schema);
    }

    internal JsonSchemaEvaluation Evaluate(
        Uri schemaUri,
        JsonElement instance,
        CultureInfo culture)
    {
        ArgumentNullException.ThrowIfNull(schemaUri);
        ArgumentNullException.ThrowIfNull(culture);
        if (!schemas.TryGetValue(schemaUri.AbsoluteUri, out var schema) ||
            !schemaType.IsInstanceOfType(schema) ||
            !buildOptionsType.IsInstanceOfType(buildOptions))
        {
            throw new InvalidOperationException("The exact schema was not registered.");
        }

        var options = Activator.CreateInstance(evaluationOptionsType) ??
            throw new InvalidOperationException("JsonSchema.Net EvaluationOptions could not be created.");
        RequireProperty(evaluationOptionsType, "Culture").SetValue(options, culture);
        RequireProperty(evaluationOptionsType, "OutputFormat").SetValue(options, listOutputFormat);
        var result = evaluate.Invoke(schema, [instance, options]) ??
            throw new InvalidOperationException("JsonSchema.Net did not return an evaluation result.");
        var resultType = result.GetType();
        var isValid = (bool)(RequireProperty(resultType, "IsValid").GetValue(result) ??
            throw new InvalidOperationException("JsonSchema.Net did not expose validity."));
        if (isValid)
        {
            return new JsonSchemaEvaluation(true, []);
        }

        var toList = resultType.GetMethod(
            "ToList",
            BindingFlags.Public | BindingFlags.Instance,
            Type.EmptyTypes) ??
            throw new InvalidOperationException("JsonSchema.Net list output is unavailable.");
        toList.Invoke(result, null);
        var locations = ImmutableArray.CreateBuilder<string>();
        CollectInvalidLocations(result, locations);
        return new JsonSchemaEvaluation(
            false,
            locations.Distinct(StringComparer.Ordinal).ToImmutableArray());
    }

    private static void CollectInvalidLocations(
        object result,
        ImmutableArray<string>.Builder locations)
    {
        var resultType = result.GetType();
        var itemIsValid = (bool)(RequireProperty(resultType, "IsValid").GetValue(result) ?? false);
        if (!itemIsValid)
        {
            locations.Add(
                RequireProperty(resultType, "InstanceLocation").GetValue(result)?.ToString() ??
                string.Empty);
        }

        if (RequireProperty(resultType, "Details").GetValue(result) is not IEnumerable details)
        {
            return;
        }

        foreach (var detail in details)
        {
            if (detail is not null)
            {
                CollectInvalidLocations(detail, locations);
            }
        }
    }

    private static Type RequireType(Assembly assembly, string name) =>
        assembly.GetType(name, throwOnError: true, ignoreCase: false) ??
        throw new TypeLoadException(string.Concat("Required JsonSchema.Net type is unavailable: ", name));

    private static PropertyInfo RequireProperty(Type type, string name) =>
        type.GetProperty(name, BindingFlags.Public | BindingFlags.Instance) ??
        throw new InvalidOperationException(
            string.Concat("Required JsonSchema.Net property is unavailable: ", name));
}
