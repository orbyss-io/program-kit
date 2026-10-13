using System.Text.Json;
using LabelOwner.Core;

if (args is ["export"])
{
    // The build tool chooses the wire representation; Core owns all policy values.
    var controls = Enumerable.Range(0, 65536).Where(unit => DisplayLabels.IsForbiddenRawCharacter((char)unit)).ToArray();
    var ranges = new List<int[]>();
    foreach (var unit in controls)
    {
        if (ranges.Count == 0 || ranges[^1][1] + 1 != unit) ranges.Add([unit, unit]);
        else ranges[^1][1] = unit;
    }
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        schemaVersion = 1, owner = DisplayLabels.Owner, contractId = DisplayLabels.ContractId,
        contractVersion = DisplayLabels.ContractVersion,
        rules = new Dictionary<string, object>
        {
            ["displayLabel"] = new
            {
                ruleId = DisplayLabels.RuleId, ruleVersion = DisplayLabels.RuleVersion,
                normalizationOrder = DisplayLabels.NormalizationOrder,
                trimCodeUnits = DisplayLabels.TrimCodeUnits, rejectedRawCodeUnitRanges = ranges,
                lengthUnit = DisplayLabels.LengthUnit,
                minimumLength = DisplayLabels.MinimumLength, maximumLength = DisplayLabels.MaximumLength
            }
        }
    }));
    return;
}
if (args is ["evaluate"])
{
    var inputs = JsonSerializer.Deserialize<string?[]>(await Console.In.ReadToEndAsync())!;
    Console.WriteLine(JsonSerializer.Serialize(inputs.Select(raw =>
    {
        var normalized = DisplayLabels.Normalize(raw);
        return new { valid = normalized is not null, value = normalized, digest = normalized is null ? null : DisplayLabels.Digest(normalized) };
    })));
    return;
}
throw new ArgumentException("Expected export or evaluate.");
