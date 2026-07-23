namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Composition;

[TestClass]
public sealed class ForeignOriginSourceJsonContextTests
{
    [TestMethod]
    public void GeneratedContextOwnsItsStringMetadata()
    {
        var context = ForeignOriginSourceJsonContext.Default;
        var typeInfo = context.GetTypeInfo(typeof(string));
        Assert.IsNotNull(typeInfo);
        Assert.AreSame(context, typeInfo.OriginatingResolver);
    }
}
