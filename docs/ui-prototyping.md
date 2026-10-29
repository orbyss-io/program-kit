# Consumer UI prototypes

Use the installed UI skill to explore an application's pages, navigation, layouts, branding and
components from its existing product intent and journeys. An intake-complete consumer can start
directly; the skill reuses the workspace's actors, roadmap, architecture and settled design choices.
Useful documents are enough, including projects without an architecture JSON map.

In Codex, for example:

```text
$speckit-program-kit-governance-ui Preview the journeys in this workspace as a connected UI.
Use fictional data and local interactions. Include the page structure, menus and navigation.
Research suitable free components for our diagram editor and explain the relevant tradeoffs.
```

The portable command is `speckit.program-kit-governance.ui`. This is a shipped consumer capability,
not a Program Kit maintainer skill. The same command retains its production UI profile operations;
a prototype request takes the separate design path.

The agent proposes the page structure and builds an editable local prototype, normally in a
consumer-owned `prototypes/<name>/` directory. Broad previews can represent many journeys with
lightweight pages and deepen the interactions being reviewed. The agent identifies missing or
unfinished areas, opens the preview when local tools support it, and explains how to run it.
Sample records, role switches, forms and specialized components can work entirely in local state.

Research starts with the interaction the page needs. Frameworks and component providers are
compared using current primary sources, relevant features, licenses/free-tier boundaries,
frontend fit, styling and accessibility. Existing consumer decisions remain the starting point;
there is no fixed provider catalog or required framework. A specialized component should be tried
in its page context, with any placeholder or unverified claim disclosed.

Continue in the same conversation, for example:

```text
Show a top navigation alternative. Keep our branding and enlarge the diagram canvas.
Try the other editor component on this page so we can compare the interaction.
```

The prototype, selected assets and short design note retain the reviewed experience, research
links, decisions, simulated behavior and gaps. These provide references for later feature
specifications and implementation. Choosing a prototype framework does not silently change the
production stack. Existing shared UI profiles and generated production output keep their owners.

UI decisions also arise naturally during product and feature conversations: when a journey exposes
a consequential navigation, information, action or recovery choice, the agent discusses it there.
Sketches and prototypes are available when helpful; each journey does not require generated screens.

Once you choose a design, its prototype and note are linked from product intent or the relevant
feature document. The note records what you chose and what remains illustrative or exploratory.
Specification reuses the agreed experience; planning explains how to implement it, and tasks carry
the relevant reference forward. The agent inspects the affected design rather than redesigning it.

Existing reviews consider how later decisions affect what you see, understand or do. A new approval
step, for example, may warrant a focused journey revision; an internal refactor preserving the
experience needs no new design decision. Consequential changes return to the design conversation,
with their reason and affected preview where useful, preserving unrelated choices. At the normal
runnable story review, compare the actual implementation with the agreed experience. After delivery,
the implemented UI and current decisions become the reference; prototypes remain available for
rationale and exploration without becoming a second application to maintain.

This follows the emphasis on shared intent, reusable components and ongoing collaboration in
[Figma's handoff guidance](https://www.figma.com/blog/the-designers-handbook-for-developer-handoff/)
and [agent guidance](https://help.figma.com/hc/en-us/articles/34855090823063-MCP-server-best-practices).
[GOV.UK's prototyping guidance](https://www.gov.uk/service-manual/design/making-prototypes) also
distinguishes exploring a design from engineering production code. These inform the approach;
the consumer chooses its design tools and frontend.

No backend, identity provider, database, full production acceptance suite or additional intake
approval is needed to explore a design. Use existing installed tools and ordinary project packages.
Real services, publication and implementation remain separately scoped work. Prototype review
establishes the presented design choices; runtime integration and implementation acceptance follow
through the consumer's ordinary delivery process.
