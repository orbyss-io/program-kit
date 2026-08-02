using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterExtensionContractTests
{
    private const string ConfigPath = ".specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml";

    [TestMethod]
    public void Extension_registers_exact_conditional_non_authorizing_hooks()
    {
        string root = Path.Combine(TestRepository.Root, "extensions", "orbyss-program-kit-adapter");
        JsonObject manifest = RestrictedYaml.Parse(File.ReadAllText(Path.Combine(root, "extension.yml")));
        JsonObject provides = manifest["provides"]!.AsObject();
        string[] commands = provides["commands"]!.AsArray().OfType<JsonObject>()
            .Select(command => command["name"]!.GetValue<string>())
            .ToArray();
        CollectionAssert.AreEquivalent(new[]
        {
            "speckit.program-kit.doctor", "speckit.program-kit.activate", "speckit.program-kit.disable",
            "speckit.program-kit.handoff", "speckit.program-kit.validate", "speckit.program-kit.prepare",
            "speckit.program-kit.explain", "speckit.program-kit.construct", "speckit.program-kit.evaluate",
            "speckit.program-kit.cleanup",
        }, commands);

        JsonObject[] hooks = provides["hooks"]!.AsArray().OfType<JsonObject>().ToArray();
        AssertHook(hooks, "after_plan", "speckit.program-kit.handoff", optional: true);
        AssertHook(hooks, "after_tasks", "speckit.program-kit.validate", optional: true);
        AssertHook(hooks, "before_implement", "speckit.program-kit.validate", optional: false);
        AssertHook(hooks, "after_implement", "speckit.program-kit.prepare", optional: true);
        Assert.IsTrue(hooks.All(hook => hook["command"]!.GetValue<string>() is
            "speckit.program-kit.handoff" or "speckit.program-kit.validate" or "speckit.program-kit.prepare"));

        foreach (string command in new[] { "handoff", "validate", "prepare" })
        {
            string instruction = File.ReadAllText(Path.Combine(root, "commands", $"{command}.md"));
            string normalized = string.Join(' ', instruction.Split((char[]?)null, System.StringSplitOptions.RemoveEmptyEntries));
            StringAssert.Contains(normalized, "Resolve applicability first");
            string lower = normalized.ToLowerInvariant();
            StringAssert.Contains(lower, "never initializ");
            StringAssert.Contains(lower, "record");
            StringAssert.Contains(lower, "authority");
            StringAssert.Contains(lower, "select");
            StringAssert.Contains(lower, "grant");
            StringAssert.Contains(lower, "construct");
            Assert.IsFalse(instruction.Contains("program-kit init", System.StringComparison.OrdinalIgnoreCase));
            Assert.IsFalse(instruction.Contains("authority record", System.StringComparison.OrdinalIgnoreCase));
        }
        StringAssert.Contains(File.ReadAllText(Path.Combine(root, "commands", "validate.md")), "Inherited `assist`");
    }

    [TestMethod]
    public void Every_command_binds_the_project_config_and_rejects_ambient_semantics()
    {
        string root = Path.Combine(TestRepository.Root, "extensions", "orbyss-program-kit-adapter");
        foreach (string path in Directory.EnumerateFiles(Path.Combine(root, "commands"), "*.md"))
        {
            string instruction = File.ReadAllText(path);
            StringAssert.Contains(instruction, ConfigPath, Path.GetFileName(path));
            Assert.IsTrue(instruction.Contains("environment", System.StringComparison.OrdinalIgnoreCase), Path.GetFileName(path));
        }

        JsonObject template = RestrictedYaml.Parse(File.ReadAllText(Path.Combine(root, "config", "orbyss-program-kit-adapter-config.template.yml")));
        Assert.AreEqual("assist", template["activation"]!["defaultMode"]!.GetValue<string>());
        Assert.IsFalse(template.ContainsKey("profileDefault"));
        Assert.IsFalse(template["activation"]!.AsObject().ContainsKey("profileDefault"));
    }

    private static void AssertHook(JsonObject[] hooks, string eventName, string command, bool optional)
    {
        JsonObject hook = hooks.Single(item => item["event"]!.GetValue<string>() == eventName);
        Assert.AreEqual(command, hook["command"]!.GetValue<string>());
        Assert.AreEqual(optional, bool.Parse(hook["optional"]!.GetValue<string>()));
    }
}
