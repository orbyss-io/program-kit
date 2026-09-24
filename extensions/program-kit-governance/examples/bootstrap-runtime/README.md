# Published-host compatibility example

This synthetic probe uses Foundation 0.2.2 and CShells 0.0.29-preview.147. It never
builds a host image or consumer product. `Core` owns the port; `Feature` contributes
two selectable implementations and a small HTTP adapter. `Boundary` inspects the
compiled Core assembly and rejects a deliberately injected ASP.NET dependency.

The caller supplies `runtime-inputs.json` with an independently verified `hostImage`
digest and contract-bound copies of these sources plus `compatibility_process.py`
as `bounded_process.py`. The native compatibility coordinator performs renew and
locked restore for the Core, Feature and Boundary projects. Only then does
`runtime_probe.py` build/pack the synthetic capabilities and run the published host.
It verifies actual shell resolution, replacement/isolation, JSON admission, response
headers, real OpenAPI output and unchanged-bundle restart. The caller owns pulling
the exact image. Containers and temporary local-feed extraction are cleaned up.

System.Text.Json is an explicit locked runtime-feed dependency for the OpenAPI
package: a framework-provided compile reference alone does not supply an archive
to Nuplane's local-feed dependency resolver. Package archives remain read-only;
the local `.installed` extraction directory is a separate writable runtime mount.

`forms_probe.py` is the runner used by the maintained public-component integration
fixtures: it requires their contract-bound `components/` and `web/` sources.
Do not run it without those inputs or substitute handwritten releases for the
public producer/admission/React mechanisms. The maintainer recovery helper prepares
the full fictional-trial fixture, while ordinary consumers adapt only applicable
examples to their reviewed prerequisite scope.

Source evidence: Foundation tag v0.2.2 commit
`8d60cdd55e7fb9056c83d614786667c04ef78bdf`, public host and WebDefaults/OpenAPI
feature implementations; Nuplane preview.61 commit
`c292a10390ada26da54865d46820d3ec327c8888`, local-feed resolver. Compiler, HTTP
and injected-negative results, not these examples alone, establish a tested claim.
