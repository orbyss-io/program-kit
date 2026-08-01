using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Authority;

public sealed record AuthorityCondition(string Kind, JsonObject Value);

public sealed record AuthorityGrant(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity Identity,
    GovernedIdentity Provider,
    string Issuer,
    string Assurance,
    IReadOnlyList<GovernedIdentity> Subjects,
    IReadOnlyList<FactoryOperation> Operations,
    IReadOnlyList<RequestedEffect> Effects,
    string RequestBinding,
    string? LockBinding,
    IReadOnlyList<AuthorityCondition> Conditions,
    DateTimeOffset NotBefore,
    DateTimeOffset NotAfter,
    ArtifactReference RevocationReference,
    ArtifactReference Provenance,
    JsonObject CanonicalDocument);

public sealed record AuthorityDecision(
    AuthorityGrant Grant,
    string RequestBinding,
    string OperationClosureDigest,
    string ReviewDigest,
    string RevocationDigest);
