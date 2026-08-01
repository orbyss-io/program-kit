using System;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Providers.DotNet.Composition.HttpEndpoints;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class KernelMechanicsTests
{
    [TestMethod]
    public void Canonical_json_orders_keys_and_has_no_layout_bytes()
    {
        byte[] bytes = CanonicalJson.Encode(new JsonObject { ["z"] = 1, ["a"] = "x" });
        CollectionAssert.AreEqual(Encoding.UTF8.GetBytes("{\"a\":\"x\",\"z\":1}"), bytes);
    }

    [TestMethod]
    [DataRow("{\"a\":1,\"a\":2}")]
    [DataRow("{\"a\":1.0}")]
    [DataRow("{\"a\":1e2}")]
    [DataRow("{\"a\":9007199254740992}")]
    public void Canonical_json_rejects_ambiguous_values(string value) => Assert.ThrowsExactly<JsonException>(() => CanonicalJson.Parse(Encoding.UTF8.GetBytes(value)));

    [TestMethod]
    [DataRow("../escape")]
    [DataRow("C:\\root")]
    [DataRow("CON/file")]
    [DataRow("a/../b")]
    public void Logical_paths_fail_closed(string value) => Assert.ThrowsExactly<ArgumentException>(() => LogicalPaths.Normalize(value));

    [TestMethod]
    public void Restricted_yaml_and_json_have_the_same_canonical_projection()
    {
        JsonNode yaml = new RestrictedYamlParser().Parse(Encoding.UTF8.GetBytes("z: value.with.period\na: 1\n"));
        JsonNode json = CanonicalJson.Parse(Encoding.UTF8.GetBytes("{\"a\":1,\"z\":\"value.with.period\"}"));
        CollectionAssert.AreEqual(CanonicalJson.Encode(json), CanonicalJson.Encode(yaml));
    }

    [TestMethod]
    [DataRow("a: &anchor value\nb: *anchor\n")]
    [DataRow("a: 1.5\n")]
    [DataRow("a: 1e2\n")]
    public void Restricted_yaml_rejects_nonportable_constructs(string value) => Throws(() => new RestrictedYamlParser().Parse(Encoding.UTF8.GetBytes(value)));

    [TestMethod]
    public void Endpoint_assembly_is_order_independent_and_rejects_duplicates()
    {
        EndpointContribution a = new("a", "GET", "/a", "A", null);
        EndpointContribution b = new("b", "GET", "/b", "B", null);
        CollectionAssert.AreEqual(new[] { a, b }, EndpointAssembler.Resolve(new[] { b, a }).ToArray());
        Assert.ThrowsExactly<InvalidOperationException>(() => EndpointAssembler.Resolve(new[] { a, a with { Identity = "other", Route = "a/" } }));
    }

    [TestMethod]
    public void Diagnostic_catalog_is_complete_and_unique()
    {
        Assert.AreEqual(26, DiagnosticCatalog.Entries.Count);
        Assert.AreEqual(26, DiagnosticCatalog.Entries.Keys.Distinct(StringComparer.Ordinal).Count());
    }

    private static void Throws(Action action)
    {
        try
        {
            action();
            Assert.Fail("Expected an exception.");
        }
        catch (AssertFailedException)
        {
            throw;
        }
        catch { }
    }
}
