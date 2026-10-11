namespace ProgramKit.Foundation.TestSupport;

/// <summary>Native provider ordinal/name for an effective configuration input; no configured value is retained.</summary>
public sealed record SettingSource(string Path, int? ProviderOrdinal, string Provider);
