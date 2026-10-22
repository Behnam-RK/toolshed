# Smart sizing

Spend review effort in proportion to the change. Decide once, in a line or two,
from the size numbers below; do not read the diff to decide. Explicit
`--max-reviewers`, `--max-rounds`, `--model` and `--lenses` win per setting.

## Measure

Code: `git diff <base> --shortstat` and `--name-only`, counting uncommitted
changes. Prose or named files: `wc -l` over them. Lines = insertions +
deletions.

## Tier

The higher tier of lines and files wins; a risky path bumps one tier.

| Tier | Lines | Files | Reviewers | Rounds |
|---|---|---|---|---|
| Small | < 200 | ≤ 5 | 1 | 2 |
| Medium | < 800 | any | 1–2 | 2–3 |
| Large | < 2000 | any | 2 | 3–4 |
| Max | ≥ 2000 | any | 2–3 | 4–5 |

Inside a range, take the low end for repetitive or single-module changes and
the high end for entangled or cross-module ones.

**Risky**: auth, shell or exec, SQL, secrets, input parsing, migrations,
CI or deploy config.

## Model

`sonnet` only for a Small, plain change that is mechanical: renames, moves,
formatting, comment or typo edits, version bumps, generated or dependency
churn. Never `haiku`. Anything else keeps the normal reviewer-model rule.
