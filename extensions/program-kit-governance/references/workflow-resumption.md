# Retired founding workflow: historical evidence and migration

The bootstrap workflow is retired. Newly upgraded `workflow_lifecycle.py run`, `resume`, `reopen`
and internal `step` commands refuse with the supported
`$speckit-program-kit-governance-product-intake` route. They never launch workers, rewrite saved
states or convert incomplete runs into completed founding. The bundle installs no workflow.

Upgrade removes only owned active workflow registration/files through native ownership checks.
Customized owned files require explicit reconciliation. Preserve saved runs, snapshots, old proof
bytes, authored artifacts, accepted decisions and consumer locks. A paused/failed old run remains
paused/failed. Never automatically restart or convert an actual consumer.

Use product-intake to inspect useful current intent and artifacts in the existing session, reopen
only consequential uncertainties, retain provenance and explicitly review current named decisions.
Intake confirmation, constitution ratification and ADR/map acceptance remain distinct. Then continue
directly to the selected first feature intake. See [focused product founding](product-founding.md).

`workflow_lifecycle.py validate-completion` remains a read-only inspector for old completed engine
bindings. It requires the actual saved completed run and recorded lineage; it does not supply
current founding acceptance, runtime compatibility or upgrade authority. Hashes cannot substitute
for human acceptance or actual executed verification.
