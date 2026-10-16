# Native evaluated restore ownership

The default literal adapter diagnoses custom/imported layouts instead of guessing
standard lock/assets paths. Opt into the native adapter with an explicit current
`eng/restore-graph.json`:

```json
{
  "schemaVersion": 1,
  "adapter": "native-msbuild",
  "configuration": "Debug",
  "sdkVersion": "10.0.402"
}
```

Use the actual selected exact SDK version. It must already be prepared and match
the recorded toolchain. This file selects one project restore context; commands
restore its actual project roots directly, including solution-selected members,
forward references and reverse dependents. It does not borrow a solution's custom
configuration remapping. Reference metadata that changes evaluation contexts,
framework-specific output identities and consumer restore-target overrides/hooks
need a separately admitted adapter and fail here.

The adapter uses targetless SDK preprocessing and item/property evaluation before
NuGet's `GenerateRestoreGraphFile` metadata target. It admits current contained
C#/F#/VB owners before graph traversal, binds expanded imported bytes, then checks
the native graph against those references and evaluated output properties. It
verifies imports again after inspection. Installed SDK/workload/package imports
remain visible in expanded-source hashes; retired/scratch project imports and
unadmitted external source imports fail. No application build/run or historical
business-code target is requested. Consumer restore hooks are refused before the
metadata target. Keep arbitrary/paid operations out of deterministic build policy.

Custom `NuGetLockFilePath` and early `MSBuildProjectExtensionsPath`/intermediate
policy must agree with actual NuGet output locations. Setting a property too late
does not relocate a native output. Multiple active owners need distinct outputs,
including independent owners outside the affected dependency closure. Protected
records, retired roots, source documents and non-lock JSON cannot become restore
destinations. Inherited/dynamic contexts this adapter cannot qualify are errors.

Restore planning, reviewed requests, execution progress, output inventories,
verification and upgrade renewal use the same closure. Custom JSON lock names are
included in native evidence, not omitted because they are not `packages.lock.json`.
Upgrade discovers current custom locks through this adapter, while original
reset-bound retirement uses the .NET retained-input reader. Missing active locks
need reviewed native renewal; absence is never authenticated retirement.

Every evaluation retains commands, both streams, expanded sources, native metadata
and its scoped outcome under `artifacts/program-kit/restore-graph-runs/<unique>/`.
The canonical graph digest normalizes JSON map order; raw emitted bytes remain in
that run. Graph inspection supplies output ownership, not successful restore or
application acceptance. Complete the normal reviewed renew and LockedMode flow.

Public contracts: [MSBuild targetless item/property evaluation](https://learn.microsoft.com/en-us/visualstudio/msbuild/evaluate-items-and-properties),
[NuGet lock file configuration](https://learn.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files#locking-dependencies).
