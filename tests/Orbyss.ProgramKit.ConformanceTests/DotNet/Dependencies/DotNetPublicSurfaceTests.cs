using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Dependencies;

[TestClass]
public sealed class DotNetPublicSurfaceTests
{
    [TestMethod]
    public void PublicSurfaceContainsNoMetadataPackageAnnotationsOrDomContracts()
    {
        var assembly = typeof(DotNetShellDocument).Assembly;
        var exported = assembly.GetExportedTypes();

        Assert.DoesNotContain(
            static type =>
                type.Namespace?.Contains(".Metadata", StringComparison.Ordinal) == true,
            exported);
        Assert.DoesNotContain(
            static type =>
                typeof(Attribute).IsAssignableFrom(type),
            exported);
        foreach (var type in exported)
        {
            var contractTypes = type
                .GetConstructors()
                .SelectMany(static constructor => constructor.GetParameters())
                .Select(static parameter => parameter.ParameterType)
                .Concat(type.GetProperties().Select(static property => property.PropertyType));
            Assert.DoesNotContain(
                static contractType => ContainsDomType(contractType),
                contractTypes,
                type.FullName);
        }
    }

    [TestMethod]
    public void ConsumerProjectionTypesDoNotEnumerateResultOrContinuationSemantics()
    {
        var names = typeof(DotNetOperationBinding).Assembly
            .GetExportedTypes()
            .Select(static type => type.Name)
            .ToArray();

        Assert.DoesNotContain(
            static name => name.Contains("SemanticImage", StringComparison.Ordinal),
            names);
        Assert.DoesNotContain(
            static name => name.Contains("ContinuationResult", StringComparison.Ordinal),
            names);
        Assert.DoesNotContain(
            static name => name.Contains("ResultKind", StringComparison.Ordinal),
            names);
    }

    private static bool ContainsDomType(Type type)
    {
        if (type == typeof(JsonElement) ||
            type == typeof(JsonNode) ||
            typeof(JsonNode).IsAssignableFrom(type))
        {
            return true;
        }

        return type.IsGenericType &&
               type.GetGenericArguments().Any(ContainsDomType);
    }
}
