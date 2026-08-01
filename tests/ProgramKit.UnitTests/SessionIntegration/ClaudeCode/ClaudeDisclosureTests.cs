using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeDisclosureTests
{
    [TestMethod]
    public void Observation_boundary_has_no_raw_output_transcript_prompt_reasoning_or_physical_path_field()
    {
        string[] propertyNames = typeof(ClaudeObservationInput).GetProperties().Select(static item => item.Name).ToArray();
        string[] forbidden = { "Raw", "Output", "Transcript", "Prompt", "Reasoning", "Credential", "PhysicalPath", "Exception" };
        foreach (string value in forbidden)
            Assert.IsFalse(propertyNames.Any(name => name.Contains(value, StringComparison.OrdinalIgnoreCase)), value);
    }
}
