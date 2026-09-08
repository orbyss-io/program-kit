# ProgramKit NuGet package retirement

The published `ProgramKit.*` packages are legacy component identities. Their replacements are the
independently versioned `Orbyss.Foundation.*`, `Orbyss.Forms.*`, and `Orbyss.Localization.*`
families. Program Kit itself remains an AI extension and does not publish a NuGet runtime.

NuGet.org does not permanently delete ordinary packages. Its delete command unlists an exact
package version: new consumers no longer discover it in normal search, while existing consumers can
still restore the exact version. The immutable IDs therefore remain reserved and recoverable.

The exact retirement inventory is `operations/nuget/program-kit-retirement.json`: 49 package IDs
and 213 published versions, queried from NuGet.org on 2026-09-07. The operation is deliberately
gated. Before it mutates NuGet.org, it verifies that all 22 Foundation packages at `0.1.0`, all 15
Forms packages at `0.1.1`, and all 13 Localization packages at `0.1.1` are public and listed.

## Local retirement only

Retirement is intentionally not a GitHub workflow and must never be added to the Program Kit release
graph. After all component releases and Program Kit `v0.10.0` have succeeded, use a local NuGet.org
API key whose package glob covers `ProgramKit.*` and grants unlist permission. Do not store or print
the key.

For a local, non-mutating audit:

```powershell
python scripts/retire_programkit_nuget.py --verify-public
```

The executing form additionally requires an unlist-scoped `NUGET_API_KEY` and the exact confirmation
`UNLIST ALL PROGRAMKIT PACKAGES`. It waits for NuGet.org propagation and succeeds only when all 213
inventoried versions report unlisted. Do not store that key in the repository or print it in logs.

```powershell
$secureKey = Read-Host 'NuGet.org API key' -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:NUGET_API_KEY =
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)

    python .\scripts\retire_programkit_nuget.py `
        --verify-public `
        --execute `
        --confirmation 'UNLIST ALL PROGRAMKIT PACKAGES'

    if ($LASTEXITCODE -ne 0) {
        throw "Package retirement failed with exit code $LASTEXITCODE."
    }
}
finally {
    Remove-Item Env:NUGET_API_KEY -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    Remove-Variable secureKey, keyPointer -ErrorAction SilentlyContinue
}
```
