# Program Kit 0.9.0 compatibility report

0.9.0 is an intentional runtime-composition change. Applications continue to run on the external
`ProgramKit.Host`, but web behavior is supplied by version-matched feature packages selected in
`.program-kit/web-profile.shells.json`.

The BFF-cookie and SPA-PKCE profiles retain their existing configuration meanings and browser/API
contracts. The runtime client-secret environment key moves to the shell configuration path:

`CShells__Shells__default__Configuration__ProgramKit__Web__ClientSecret`

Synchronization is desired-state and transactional. Unmodified Program Kit profile contributions
move safely between profiles; a consumer-modified retiring file is reported as a conflict and no
other file is changed. A versioned migration removes only known historical hashes of SPA files that
0.8.11 could leave behind without state ownership.

The default Problem Details and OpenAPI features are explicit shell features. A consumer can set
`ProgramKit.Web.ProblemDetails` to `false` in `shells.json` and activate its own exception-handling
feature; no response-body policy is hard-coded in `ProgramKit.Host`.
