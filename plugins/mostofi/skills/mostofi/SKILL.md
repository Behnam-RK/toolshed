---
name: mostofi
description: "Keep docs true to code and capture decisions as ADRs. Use when code changed and READMEs, docstrings, comments, changelogs or ADRs may be stale (PRs, reviews, renames, resolved TODOs, 'update the docs', 'doc review'), or when a decision is made or asked about ('record this decision', 'we chose X over Y', 'why did we pick X?'). Not for authoring new end-user docs."
---

# Mostofi — docs & ADR steward

Two jobs, one surface (READMEs, ADRs, changelogs, docstrings, comments):
keep existing docs honest after code changes, and record hard-to-reverse
decisions. Offer a pass proactively; stale docs and unrecorded decisions fail
silently.

## Rules

- **Repo policy is binding.** A documentation guide, code-style doc,
  `AGENTS.md` or `CONTRIBUTING.md` that states thresholds or rules overrides
  every default here, stricter or not. Detect and match its voice, docstring
  style and ADR layout. Real cases: `references/overrides.md`.
- **Truth first.** A doc contradicting the code is a defect: fix or delete it.
- **Why over what.** Keep intent, constraints, trade-offs, gotchas; delete
  narration of what the code shows. A docstring that paraphrases the name is a
  naming failure — fix the name. A block long because the code is tangled is a
  refactor signal: flag the code, don't polish the prose.
- **One source of truth.** Check for an existing doc before writing; fold
  duplicates in and point at them.
- **History is append-only.** Changed decisions are *Superseded* (linking the
  replacement), answered questions *Resolved* with how — never deleted.
- **Minimal diff.** Touch only what is stale or missing. A clean pass is valid.
- **Runtime-surfaced docstrings** (MCP/tool descriptions, CLI `--help`,
  GraphQL descriptions) are API: exempt from trimming, not from truth.

| | Steward pass | Decision capture |
|---|---|---|
| Trigger | code changed / doc pass asked | decision made / record asked |
| Output | edits to existing docs and in-code prose | new numbered ADR + index row |
| Consent | apply directly, then report | **draft, write only after explicit approval** |

## Steward pass

0. **Conventions.** Find the repo's doc rules. Defaults if none: docstrings
   only where name + signature + types can't carry meaning (exported APIs,
   subclass contracts, side effects, non-trivial module headers; `_private`
   only when non-obvious). `comment-block` warns over **3 lines** (advisory:
   reread); over **10 lines** (docstring over ~3) carrying real knowledge
   must be *relocated*, not truncated.
1. **Scope.** Diff against base (`git diff --name-only <base>...HEAD`); note
   added/renamed/removed symbols and config. Run
   `mostofi scan [--base <ref>] [--json] [--root <path>]` — advisory leads,
   exit 0. `mostofi check` is the blocking gate on the same `.docs.toml`;
   `mostofi --explain <rule>` explains one rule.
2. **Review** each surface: does it match the code, is anything new
   unrecorded, anything stale or redundant? Per-surface checklist:
   `references/review-checklist.md` (read when reviewing). On ADRs: advance
   statuses, mark supersessions with links, fix outgrown rationale, and you may
   relocate rationale already written in code. A decision recorded *nowhere*
   goes to Decision capture.
3. **Edit.** Append docstrings (non-obvious symbols only), config docs,
   changelog lines. Update stale prose and cross-references. Extract long
   knowledge-bearing blocks to their owning doc, leaving a pointer plus ≤3-line
   why. Dedupe. Trim narration, dead roadmap items, resolved TODOs.
   Routing table and the "no decision records in code" variant:
   `references/extraction.md` (read before extracting).
4. **Verify.** References resolve, "open" items match reality, every
   superseded ADR links a live replacement, examples still run; rescan.
5. **Report**, always: `references/report.md`. Worked cases:
   `references/examples.md` (read when a case is unclear).

For an explicit repo-wide "shrink the docs" ask, read
`references/shrink-pass.md` first.

## Decision capture

The bar is *hard to reverse*, not *important*; unsure → ask.

- **Explicit** ("record this", "create an ADR", "let's go with X"): draft it.
- **Implicit** (frameworks/libraries compared and concluded, schema, API
  shape, auth, deployment chosen by weighing options): *suggest* an ADR, wait
  for yes.
- **"Why did we pick X?"**: read the ADR index and show the entry's
  **Decision:** and **Why:**; no ADR dir → ask whether to start one; no
  match → offer to record it.
- Never invent rationale from a diff alone: flag it, draft what you can
  verify, ask the author for the rest.

Format, numbering, index, lifecycle and capture steps: `references/adr.md`
(read before drafting or editing any ADR).
