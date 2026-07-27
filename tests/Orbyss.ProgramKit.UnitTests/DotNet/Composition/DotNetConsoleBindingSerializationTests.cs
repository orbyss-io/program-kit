using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Composition;

[TestClass]
public sealed class DotNetConsoleBindingSerializationTests
{
    [TestMethod]
    public void BindingCanonicallyRoundTripsAndConformsToItsExactSchema()
    {
        ProgramKitJsonBuilder builder = new(
            new ProgramKitJsonRegistryFactory());
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(
            builder.Freeze(),
            canonicalizer);
        var profile = DotNetJsonProfiles.ShellBootstrap;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);

        var first = serializer.Write(
            binding,
            profile.Reference,
            profile.MaximumLimits);
        var roundTrip = serializer.Read<DotNetConsoleBindingDocument>(
            first.ToArray(),
            profile.Reference,
            profile.MaximumLimits);
        var second = serializer.Write(
            roundTrip,
            profile.Reference,
            profile.MaximumLimits);

        Assert.AreSequenceEqual(first.ToArray(), second.ToArray());
        Assert.AreEqual(
            binding.Operations[0].HandlerType.MetadataName,
            roundTrip.Operations[0].HandlerType.MetadataName);

        DotNetSchemaModule module = new(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var schema = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Name ==
                "dotnet-console-binding");
        JsonSchemaWorkbenchValidator validator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());

        var result = validator.Validate(
            first.ToArray(),
            module,
            schema.SchemaReference,
            profile.MaximumLimits);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static item =>
                    string.Concat(item.Path, " ", item.Message))));
    }
}
