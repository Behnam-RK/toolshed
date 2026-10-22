# House format

One format for every shaping doc. Above the divider is the **body**: short,
at product altitude, complete on its own. Below it are **appendices**: detail,
mechanism, history. Leave out any section with nothing to say.

## Skeleton

```markdown
| | |
|---|---|
| **Status** | Draft for review · Shape agreed |
| **Owner** | who decides |
| **Author** | who wrote it |
| **Reviewers** | who must read it |
| **Decide by** | date or milestone, or unknown |
| **Supersedes** | link to the previous version, or — |
| **Project** | Linear project |

## Headline and ask
Two or three sentences: what changes, why it matters now, and the ask —
**Decide**, **Approve** or **Inform** (name what).

## Problem
**P1 — <short name>.** One short paragraph: who feels it and what it costs.

## Solution
The approach in a paragraph or two: what users or the team see before and
after. Then:

| Problem | Resolved by |
|---|---|
| P1 | D1, D3 |
| P2 | deferred: why |

## Decisions
| # | Decision | In plain terms |
|---|---|---|
| D1 | what was chosen | what it means for the reader |

### Open: D4 — <question>
| Option | Benefit | Cost |
|---|---|---|
| A (recommended) | … | … |
| B | … | … |
Recommendation and the evidence for it, or what is missing to make one.
**Owner:** name · **Decide by:** date or unknown

## Risks
| Risk | Affects | Lasting? | Mitigation |
|---|---|---|---|

## Out of scope
- Boundaries a reader might otherwise assume are included.

---

## Appendix A — What changed from vN-1 (revisions only)
| Comment (author) | Answer | Change in vN |
|---|---|---|

## Appendix B — Engineering detail
## Appendix C — Rejected alternatives
## Appendix D — Glossary
```

## Rules

**Altitude.** The body names no classes, services, endpoints, flags, files,
tables or code. Say what a user or the team notices, by the product's own
names. Test each body sentence: would a PM act differently knowing this? No →
appendix, or cut. Appendix B holds the mechanism, linked PRs and ADRs.

**The body stands alone.** A reader who stops at the divider can still judge
and decide. An appendix adds how, never a fact the body depends on. When the
body needs depth, one sentence plus a link: "see Appendix B".

**Decisions.** A decision is Decided or Open; a recommendation stays Open
until the owner accepts it. Decided rows say what was chosen and what it means
in plain terms; the alternatives it beat go to Appendix C, one line each with
why they lost. Open decisions keep the losing options in the table with their
cost. Recommend only when the evidence supports it. Number D#s in reading
order: Decided first, then Open.

**Candor.** Built is not shipped: say which, and give every unfinished item a
`Missing:` line naming what remains. A risk states what could happen, who or
what it affects, whether it lasts, and how it is mitigated or will be checked.
Bad news that is the main point goes in the headline. Label unverified claims
as assumptions.

**Concise.** No fixed word count; every sentence earns its place. One
paragraph per problem, one row per decision. No history of how the work was
done, no closing summary, no restating the headline.

**Language.** Simple English unless asked otherwise: short sentences, common
words, exact technical terms, one term per concept. Define a term in the
glossary only when a reader would stop on it.

**Revisions.** vN is a full document, not a diff. Appendix A answers every
comment thread on vN-1, including the ones that changed nothing (say why).
