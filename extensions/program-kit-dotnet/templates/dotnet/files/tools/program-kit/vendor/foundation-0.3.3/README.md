# Released HostedPages manifest builder

Unmodified `scripts/create_hosted_manifest.py` from Foundation 0.3.3, commit
`0739892610a12f36673941dbe9718f45a38ae6cb`.

Source: https://github.com/orbyss-io/dotnet-foundation/blob/0739892610a12f36673941dbe9718f45a38ae6cb/scripts/create_hosted_manifest.py

SHA-256: `51b234a0d23ed1fe9e09483bba47e88c58398eb335582908fe9b32a558e5d06b`.
Licensed under the adjacent MIT LICENSE. Preserve exact bytes; the consumer build
verifies this hash and invokes the publisher producer on real Vite output.

The captured 0.3.3 publisher knowledge documents this script but omits its source.
Vendoring this small released build tool makes consumer builds independent of a
checkout, GitHub login or installed agent toolkit. It adds no runtime Host/library.
