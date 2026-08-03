using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterConfigurationTests
{
    [TestMethod]
    public void Feature_mode_then_project_mode_then_off_resolves_without_ambient_authority()
    {
        JsonObject config = Config("assist", Feature("applicable", "required"));
        ApplicabilityResolution explicitRequired = ApplicabilityResolver.Resolve(config, "feature-a");
        Assert.AreEqual(ActivationMode.Required, explicitRequired.Mode);
        Assert.AreEqual("feature-override", explicitRequired.Source);
        Assert.IsTrue(explicitRequired.Active);
        Assert.IsFalse(explicitRequired.BlocksWorkflow);

        config["activation"]!["features"]!["feature-a"]!.AsObject().Remove("mode");
        ApplicabilityResolution inheritedAssist = ApplicabilityResolver.Resolve(config, "feature-a");
        Assert.AreEqual(ActivationMode.Assist, inheritedAssist.Mode);
        Assert.AreEqual("project-default", inheritedAssist.Source);
        Assert.IsTrue(inheritedAssist.Active);
        Assert.IsFalse(inheritedAssist.BlocksWorkflow, "Inherited assist alone cannot block implementation.");

        config["activation"]!["features"]!["feature-a"]!["applicability"] = "disabled";
        ApplicabilityResolution disabled = ApplicabilityResolver.Resolve(config, "feature-a");
        Assert.IsFalse(disabled.Active);
        Assert.IsFalse(disabled.BlocksWorkflow);

        config["activation"]!["features"]!.AsObject().Remove("feature-a");
        config["activation"]!["defaultMode"] = "required";
        ApplicabilityResolution unresolvedRequired = ApplicabilityResolver.Resolve(config, "feature-a");
        Assert.AreEqual(Applicability.Unresolved, unresolvedRequired.Applicability);
        Assert.IsTrue(unresolvedRequired.BlocksWorkflow);

        config["activation"]!["defaultMode"] = "off";
        ApplicabilityResolution defaultOff = ApplicabilityResolver.Resolve(config, "feature-a");
        Assert.AreEqual(ActivationMode.Off, defaultOff.Mode);
        Assert.IsFalse(defaultOff.Active);
        Assert.IsFalse(defaultOff.BlocksWorkflow);
    }

    [TestMethod]
    public void Exact_feature_selection_then_lock_default_resolves_without_sole_choice_or_adapter_default_fallback()
    {
        JsonObject config = Config("assist", Feature("applicable", selection: "feature-profile"));
        JsonObject workspaceLock = Lock("workspace-profile", Selection("workspace-profile", 'a'), Selection("feature-profile", 'b'));
        EffectiveSelection explicitSelection = SelectionResolver.Resolve(config, "feature-a", workspaceLock);
        Assert.AreEqual("feature-profile", explicitSelection.Alias);
        Assert.AreEqual("feature-override", explicitSelection.Source);

        config["activation"]!["features"]!["feature-a"]!.AsObject().Remove("selection");
        EffectiveSelection inherited = SelectionResolver.Resolve(config, "feature-a", workspaceLock);
        Assert.AreEqual("workspace-profile", inherited.Alias);
        Assert.AreEqual("workspace-lock-default", inherited.Source);

        workspaceLock.Remove("defaultSelection");
        Assert.ThrowsExactly<InvalidDataException>(() => SelectionResolver.Resolve(config, "feature-a", workspaceLock));

        JsonObject duplicate = Lock("workspace-profile", Selection("workspace-profile", 'a'), Selection("workspace-profile", 'b'));
        Assert.ThrowsExactly<InvalidDataException>(() => SelectionResolver.Resolve(config, "feature-a", duplicate));

        config["profileDefault"] = "workspace-profile";
        Assert.ThrowsExactly<InvalidDataException>(() => AdapterSchemaValidator.Validate("adapter-config.schema.json", config));
    }

    [TestMethod]
    public void Reviewed_inherited_selection_remains_exactly_pinned_and_reports_later_default_divergence()
    {
        JsonObject config = Config("assist", Feature("applicable"));
        JsonObject pinned = Selection("profile-a", 'a');
        JsonObject workspaceLock = Lock("profile-a", pinned, Selection("profile-b", 'b'));
        JsonObject binding = new()
        {
            ["alias"] = "profile-a",
            ["source"] = "workspace-lock-default",
            ["selection"] = pinned.DeepClone(),
        };

        EffectiveSelection current = SelectionResolver.ResolvePinned(config, "feature-a", workspaceLock, binding);
        Assert.IsFalse(current.Diverged);
        Assert.AreEqual("profile-a", current.Alias);

        workspaceLock["defaultSelection"] = "profile-b";
        EffectiveSelection diverged = SelectionResolver.ResolvePinned(config, "feature-a", workspaceLock, binding);
        Assert.IsTrue(diverged.Diverged);
        Assert.AreEqual("profile-a", diverged.Alias, "The reviewed selection must remain pinned.");
        Assert.AreEqual("profile-b", diverged.CurrentAlias);
        Assert.IsTrue(JsonNode.DeepEquals(pinned, diverged.Selection));

        workspaceLock["selections"]![0]!["provider"]!["digest"] = Digest('c');
        Assert.ThrowsExactly<InvalidDataException>(() => SelectionResolver.ResolvePinned(config, "feature-a", workspaceLock, binding));
        workspaceLock["selections"]!.AsArray().RemoveAt(0);
        Assert.ThrowsExactly<InvalidDataException>(() => SelectionResolver.ResolvePinned(config, "feature-a", workspaceLock, binding));
    }

    private static JsonObject Config(string defaultMode, JsonObject feature) => new()
    {
        ["schema"] = "program-kit.spec-kit-adapter-config/v1",
        ["programKit"] = new JsonObject { ["invocation"] = "dotnet-tool-manifest", ["manifest"] = "program-kit.yaml", ["lock"] = "program-kit.lock.json" },
        ["activation"] = new JsonObject { ["defaultMode"] = defaultMode, ["features"] = new JsonObject { ["feature-a"] = feature } },
        ["defaultRequestedEffect"] = "none",
    };

    private static JsonObject Feature(string applicability, string? mode = null, string? selection = null)
    {
        JsonObject feature = new()
        {
            ["applicability"] = applicability,
            ["decisionSource"] = new JsonObject { ["kind"] = "human-decision", ["name"] = "feature-review" },
        };
        if (mode is not null) feature["mode"] = mode;
        if (selection is not null) feature["selection"] = selection;
        return feature;
    }

    private static JsonObject Lock(string defaultSelection, params JsonObject[] selections) => new()
    {
        ["defaultSelection"] = defaultSelection,
        ["selections"] = new JsonArray(selections),
    };

    private static JsonObject Selection(string alias, char seed) => new()
    {
        ["alias"] = alias,
        ["provider"] = Identity("factory-provider", $"provider-{seed}", seed),
        ["targetProfile"] = Identity("target-profile", $"profile-{seed}", seed),
        ["selectionAuthority"] = Identity("selection-authority", "human-review", 'f'),
    };

    private static JsonObject Identity(string kind, string name, char seed) => new()
    {
        ["authority"] = "consumer.test",
        ["kind"] = kind,
        ["name"] = name,
        ["revision"] = "1.0.0",
        ["digest"] = Digest(seed),
    };

    private static string Digest(char seed) => "sha256:" + new string(seed, 64);
}
