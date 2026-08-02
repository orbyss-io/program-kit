# Program Kit Adapter for Spec Kit

This extension connects reviewed Spec Kit feature artifacts to the public
Program Kit CLI without granting authority or coupling to Program Kit internals.

The extension requires Spec Kit `0.15.1`, Program Kit CLI
`1.0.0-alpha.2`, and the .NET 10 runtime. Its project configuration is copied
from `config/orbyss-program-kit-adapter-config.template.yml` to the exact
consumer-owned path documented by Spec Kit. Local and environment configuration
layers are deliberately non-semantic.

This source directory contains no generated binary. `eng/Pack-SpecKitAdapter.ps1`
publishes the adapter into an ignored staging directory and creates the tested
extension archive.
