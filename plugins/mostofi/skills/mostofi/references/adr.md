# ADRs

## Format

Write the shape `mostofi init` scaffolds unless the repo already has ADRs or a
`docs/adr/template.md` — then match that. A consistent log beats a canonical one.

```markdown
## ADR-NNNN: Title

**Status:** Proposed | Adopted | Deprecated | Superseded by ADR-NNNN

**Decision:** What we decided.

**Why:** Context, constraints, trade-offs.

**Rejected:** Alternatives considered and why they lost, if any.

**Trade-off:** What gets harder, and why that's accepted.
```

Anything beyond these fields explains the code, not the choice.

## Capture steps

1. **Init (first time only).** No ADR directory → ask before creating one. With
   consent, `mostofi init` writes `docs/adr/README.md` (index), `template.md`;
   hand-write only where it hasn't run. Never create files without consent.
2. **One decision per new ADR.** Three settled things = three ADRs.
3. **Context** — what forced it, which constraints. Verify against the code,
   not just the conversation.
4. **Rejected** — what was genuinely considered and why each lost. Without it
   you've recorded an outcome, not a decision.
5. **Trade-off** — honestly.
6. **Number** — scan existing ADRs and increment; watch for gaps and numbers
   claimed on other branches.
7. **Confirm, then write** — show the full draft; write
   `docs/adr/NNNN-decision-title.md` only after explicit approval. Declined →
   discard, leave no file.
8. **Index** — append a row to the ADR `README.md` in the same commit.

```markdown
| ADR | Title | Status | File |
|---|---|---|---|
| 0001 | Use Next.js as frontend framework | Adopted | [0001-use-nextjs.md](0001-use-nextjs.md) |
```

## Quality

Do: be specific ("Prisma ORM", not "an ORM"); record rationale and rejected
alternatives; state consequences honestly; under a 2-minute read; present tense.

Don't: record trivia (naming, formatting); write essays (a **Why:** over ~10
lines explains code, not choice); omit alternatives; backfill an old decision
without saying in **Why:** when it was really made (no Date field — it reads as
decided on its commit date); let superseded entries lack a replacement link.

## Lifecycle

`Proposed → Adopted → [Deprecated | Superseded by ADR-NNNN]`. Superseded links
its replacement and the replacement links back. Never edit an accepted
decision's substance — supersede it.

## With other agents

Planners: suggest capture once a proposal is actually decided, not before.
Reviewers: a PR with an architecture change and no ADR is a `Flagged:` line,
not a silent auto-write.
