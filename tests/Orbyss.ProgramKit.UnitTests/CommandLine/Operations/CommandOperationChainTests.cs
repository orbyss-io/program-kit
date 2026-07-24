using Orbyss.ProgramKit.CommandLine.Operations;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations;

[TestClass]
public sealed class CommandOperationChainTests
{
    [TestMethod]
    public void DuplicateExactRegistrationCannotBeCollapsedBeforeValidation()
    {
        ICommandOperation first =
            new UnavailableCommandOperation("graph", "test-one");
        ICommandOperation duplicate =
            new UnavailableCommandOperation("graph", "test-two");
        ICommandOperationChain tail = new CommandOperationChain(first, null);

        var exception = Assert.ThrowsExactly<InvalidOperationException>(
            () => new CommandOperationChain(duplicate, tail));

        Assert.StartsWith("PKCLI005", exception.Message, StringComparison.Ordinal);
    }
}
