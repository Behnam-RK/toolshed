# Mostofi

Keeps a repo's docs true to its code. A Claude Code plugin with:

- the `mostofi` skill — steward pass after code changes, ADR capture when a
  decision is made or asked about;
- a `UserPromptSubmit` doc-gate — on implementation-shaped prompts, a one-line
  reminder to read the conventions and a sibling first, only in a repo that has
  its routing doc or a `.docs.toml`;
- `mostofi` on PATH — a doc-budget gate measuring markdown in weighted tokens,
  with docstring/comment-block rules and stale-doc scanning.

## Install

```
/plugin marketplace add Behnam-RK/toolshed
/plugin install mostofi@toolshed
```

Needs Python 3.12+: found via `$PYTHON`, `uv python find`, then
`python3.14`…`python3.12`, `python3`.

## Use

```
/mostofi [pass|adr|why|setup] [target] [--base REF]
```

Or ask: "update the docs", "record this decision", "why did we pick X?".
`/mostofi setup` detects the repo's languages, convention docs, ADR log and
vendored trees, asks one round of questions, writes `.docs.toml` (or edits an
existing one in place), and offers to add the pinned pre-commit hook.

## Config

Per user, set in `/config` or when enabling the plugin. A repo's own doc
rules and `.docs.toml` win over these, except the doc gate: either switch
turns it off.

| Option | Default | |
|---|---|---|
| `proactivity` | `suggest` | `eager` offers a pass after code changes; `suggest` says what looks stale in one line; `on-request` waits to be asked. |
| `doc_gate` | on | Off mutes the reminder for you everywhere; `[doc-gate] enabled = false` mutes it for a repo. |
| `steward_consent` | `apply` | `propose` shows planned doc edits before writing. ADRs are always drafted for approval. |
| `setup_profile` | `default` | Profile `/mostofi setup` proposes. |

## CLI

```
mostofi check [files…]       # blocking gate, exit 1 on failure (strict with no files)
mostofi scan [--base REF]    # advisory report, exit 0 (2 if the config is broken)
mostofi init [--check]       # scaffold .docs.toml + doc guide + docs/adr/
mostofi --explain RULE       # one rule's reasoning and knobs
```

`init` flags: `--profile`, `--lang a,b`, `--exclude GLOB` (repeatable),
`--adr-dir DIR` (moves the ADR caps, collision rule and templates),
`--no-guide`, `--no-adr` (keep an existing log), `--no-docs` (both),
`--doc-gate`/`--no-doc-gate`, `--routing-doc PATH`, `--force`. `--check`
compares the landed templates with the shipped ones.

## Pin it in another repo

The repo root packages the gate as `mostofi` (extra `exact` adds tiktoken).
Pin a tagged commit, never a branch:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Behnam-RK/toolshed
  rev: <sha>  # frozen: mostofi--v1.1.0
  hooks:
    - id: mostofi
      additional_dependencies: ["tiktoken>=0.9,<1"]
```

```
uvx --from 'mostofi[exact] @ git+https://github.com/Behnam-RK/toolshed@<sha>' mostofi check
```

## `.docs.toml`

Every key is optional; `mostofi init` writes a commented starter.

| Key | Meaning |
|---|---|
| `profile` | `default` or `strict` rule severities |
| `[defaults]` `soft`, `hard` | weighted-token caps per doc (1000/1400) |
| `[[overrides]]` `pattern`, `soft`, `hard`, `rules`, `structure_rules`, `status` | per-glob caps/rules, first match wins |
| `[exclude]` `paths`, `always_exempt` | skipped / exempt paths |
| `[rules.<id>]` `severity` + knobs | `fail` / `warn` / `off`; see `--explain` |
| `[python]` `enabled`, `runtime_surfaced_decorators`, `docstring_cap`, `module_docstring_cap`, `cli_help_exempts_module` | docstring rules |
| `[comments]` `enabled`, `prefixes` | comment-block rules |
| `[corpus]` `doc_globs`, `code_globs`, `package_roots` | what is scanned |
| `[doc-gate]` `enabled`, `routing_doc`, `trigger` | the prompt hook: on/off, doc it names (default: `AGENTS.md`, else `CLAUDE.md`), ERE matched per line |
