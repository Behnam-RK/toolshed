# Dabir

Writes shaping docs for Linear projects. A shaping doc is the one a decision
is made from: a short body PMs and stakeholders can judge in minutes, with the
engineering detail in appendices. Dabir drafts v1, revises to vN from the
review comments, and publishes each version as a new Linear document, only
when you say so.

## Install

```
/plugin marketplace add Behnam-RK/toolshed
/plugin install dabir@toolshed
/plugin install linear@claude-plugins-official
```

Without the Linear plugin it still drafts, to a local markdown file, and
says publishing is unavailable.

## Use

```
/dabir [draft|revise] [project or doc]
```

Or ask: "write the shaping doc for the checkout redesign", "revise the
search shaping from the comments". With no mode it revises the project's existing
shaping doc, or drafts one if there is none.

It reads the project, its issues, earlier versions and, inside a repo, the
code; then asks only what blocks an accurate draft, as multiple-choice
questions. Everything else lands in the doc as an Open decision.

## What it writes

A properties header (status, owner, reviewers, decide-by, supersedes), then
headline and ask, problems (P#), solution, decisions (D#, Decided and Open
with options, owner and date), risks, and out of scope. The body names no
code. Detail goes below a divider: what changed and review responses (for
vN), engineering detail, rejected alternatives, glossary. The format and its
rules: `skills/dabir/references/format.md`. Run inside a repo whose
`AGENTS.md`, `CLAUDE.md` or docs state shaping conventions, and those win.

## Linear writes

Each needs its own yes:

- **Publish:** a new document `<Project> — Shaping vN` on the project.
  Earlier versions are never edited.
- **Replies:** on a revision, a reply on each thread of the previous version
  pointing to vN. Threads are never resolved.
- **Issues:** one per `Missing:` item or Open decision, picked from a list.

## Hand-offs

- **momayez:** offered before publishing, with dabir's final review checklist
  as the reviewers' brief.
- **mostofi:** in a repo with an ADR log, offered after publishing to record
  the hard-to-reverse decisions as ADRs and link them from the doc.
