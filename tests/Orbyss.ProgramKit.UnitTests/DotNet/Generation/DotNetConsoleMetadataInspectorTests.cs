using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConsoleMetadataInspectorTests
{
    [TestMethod]
    public void ExactReferenceMetadataSatisfiesEveryConsumerContract()
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            openConsole,
            assemblyPath);
        DotNetConsoleMetadataInspector sut = new();

        var result = sut.Inspect(binding, assemblyPath);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static item => item.Message)));
        Assert.IsNotNull(result.Proof);
        Assert.Contains(
            typeof(MetadataFixtureRequest).FullName,
            result.Proof.VerifiedMetadataNames);
    }

    [TestMethod]
    public void DigestDriftFailsBeforeMetadataInspection()
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            openConsole,
            assemblyPath) with
        {
            ConsumerProject = DotNetConsoleBindingTestFactory
                .MetadataBinding(openConsole, assemblyPath)
                .ConsumerProject with
            {
                ReferenceAssemblyDigest =
                    DotNetTestContractFactory.Digest('f'),
            },
        };
        DotNetConsoleMetadataInspector sut = new();

        var result = sut.Inspect(binding, assemblyPath);

        Assert.IsFalse(result.IsValid);
        Assert.IsNull(result.Proof);
    }

    [TestMethod]
    public void MissingInaccessibleGenericAndSignatureDriftFailClosed()
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            openConsole,
            assemblyPath);
        var operation = binding.Operations[0];
        binding = binding with
        {
            FeatureType = binding.FeatureType with
            {
                MetadataName = "Consumer.MissingFeature",
            },
            ValidationResultType = binding.ValidationResultType with
            {
                MetadataName =
                    typeof(GenericMetadataFixtureRequest<>).FullName ??
                    throw new InvalidOperationException(),
            },
            Operations =
            [
                operation with
                {
                    RequestType = operation.RequestType with
                    {
                        MetadataName =
                            "Orbyss.ProgramKit.ConsoleContractFixtures.Contracts.InternalMetadataFixtureRequest",
                    },
                    HandlerType = operation.ValidatorType ??
                        throw new InvalidOperationException(),
                },
            ],
        };
        DotNetConsoleMetadataInspector sut = new();

        var result = sut.Inspect(binding, assemblyPath);

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(3, result.Diagnostics.Length);
    }

    [TestMethod]
    public void ConstructorNullabilityMismatchFailsClosed()
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            openConsole,
            assemblyPath);
        var operation = binding.Operations[0];
        var parameters = operation.ConstructorParameters.ToArray();
        parameters[0] = parameters[0] with
        {
            ClrType = parameters[0].ClrType with
            {
                ReferenceNullability =
                    DotNetConsoleReferenceNullability.Nullable,
            },
        };
        binding = binding with
        {
            Operations =
            [
                operation with
                {
                    ConstructorParameters = [.. parameters],
                },
            ],
        };
        DotNetConsoleMetadataInspector sut = new();

        var result = sut.Inspect(binding, assemblyPath);

        Assert.IsFalse(result.IsValid);
    }

    [TestMethod]
    public void ForbiddenServiceLocatorConstructorFailsClosed()
    {
        var assemblyPath = typeof(MetadataFixtureRequest).Assembly.Location;
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.MetadataBinding(
            openConsole,
            assemblyPath);
        var operation = binding.Operations[0];
        binding = binding with
        {
            Operations =
            [
                operation with
                {
                    HandlerType = DotNetConsoleBindingTestFactory.Type(
                        typeof(IForbiddenMetadataFixtureHandler).FullName ??
                        throw new InvalidOperationException()),
                },
            ],
        };
        DotNetConsoleMetadataInspector sut = new();

        var result = sut.Inspect(binding, assemblyPath);

        Assert.IsFalse(result.IsValid);
    }
}
