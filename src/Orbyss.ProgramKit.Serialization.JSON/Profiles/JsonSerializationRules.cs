namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Declares the strict wire rules of a JSON serialization profile.</summary>
public sealed record JsonSerializationRules(
    bool SourceGeneratedMetadataOnly,
    bool SchemaDeclaredPropertyNames,
    bool CaseSensitiveReads,
    bool DisallowComments,
    bool DisallowTrailingCommas,
    bool DisallowUnmappedMembers,
    bool WriteNullProperties,
    bool StrictNumbers,
    bool DisallowReferencePreservation,
    bool RequireNfcStrings);
