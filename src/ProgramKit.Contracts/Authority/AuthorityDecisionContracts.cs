using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Authority;

public sealed record HumanAuthorityDecisionRecord(
    string Schema,
    string CanonicalProfile,
    ArtifactReference Proposal,
    string Reviewer,
    string Decision,
    IReadOnlyList<GovernedIdentity> Subjects,
    IReadOnlyList<FactoryOperation> Operations,
    IReadOnlyList<RequestedEffect> Effects,
    IReadOnlyList<AuthorityCondition> Conditions,
    DateTimeOffset NotBefore,
    DateTimeOffset NotAfter,
    ArtifactReference Provenance,
    DateTimeOffset RecordedAt);

public sealed record AuthorityRecordRequest(
    string Schema,
    string CanonicalProfile,
    ArtifactReference Proposal,
    ArtifactReference Decision,
    string GrantPath,
    string RevocationPath);
