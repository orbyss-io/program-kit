using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetConsoleBindingValidatorTests
{
    [TestMethod]
    public void ExactBindingReconcilesEveryCommandAndConstructorSource()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static item => item.Message)));
    }

    [TestMethod]
    public void MissingOperationBindingFailsClosed()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole) with
        {
            Operations = [],
        };
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsFalse(result.IsValid);
    }

    [TestMethod]
    public void GeneratedSymbolCollisionFailsClosed()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);
        var operation = binding.Operations[0];
        openConsole = openConsole with
        {
            Commands =
            [
                openConsole.Commands[0],
                openConsole.Commands[0] with
                {
                    OperationRevision =
                        DotNetTestContractFactory.Ref(
                            "operation",
                            "second",
                            '3'),
                    Path = ["second"],
                },
            ],
        };
        binding = binding with
        {
            Operations =
            [
                operation,
                operation with
                {
                    OperationRevision = openConsole.Commands[1].OperationRevision,
                },
            ],
        };
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsFalse(result.IsValid);
    }

    [TestMethod]
    public void TypeNullabilityAndDefaultDriftFailClosed()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);
        var operation = binding.Operations[0];
        var parameters = operation.ConstructorParameters.ToArray();
        parameters[1] = parameters[1] with
        {
            ClrType = DotNetConsoleBindingTestFactory.Type(
                "System.Int64",
                (DotNetConsoleReferenceNullability)999),
            DefaultDisposition = new DotNetConsoleDefaultDisposition(
                DotNetConsoleDefaultKind.None,
                null),
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
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(3, result.Diagnostics.Length);
    }

    [TestMethod]
    public void MissingConstructorSourceFailsClosed()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);
        var operation = binding.Operations[0];
        binding = binding with
        {
            Operations =
            [
                operation with
                {
                    ConstructorParameters =
                        operation.ConstructorParameters.RemoveAt(3),
                },
            ],
        };
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsFalse(result.IsValid);
    }

    [TestMethod]
    public void HandlerValidatorFeatureAndProjectShapesFailClosed()
    {
        var openConsole = DotNetTestContractFactory.ConsoleDocument(
            DotNetTestContractFactory.Shell());
        var binding = DotNetConsoleBindingTestFactory.Binding(openConsole);
        var operation = binding.Operations[0];
        binding = binding with
        {
            ConsumerProject = binding.ConsumerProject with
            {
                RelativeProjectPath = "../outside.csproj",
            },
            FeatureType = binding.FeatureType with
            {
                GenericArguments = default,
            },
            Operations =
            [
                operation with
                {
                    HandlerType = operation.RequestType,
                    ValidatorType = operation.RequestType,
                },
            ],
        };
        DotNetConsoleBindingValidator sut = new();

        var result = sut.Validate(binding, openConsole);

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(3, result.Diagnostics.Length);
    }
}
