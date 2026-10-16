# Mostofi

Keeps a repo's docs true to its code. A Claude Code plugin with:

- the `mostofi` skill — steward pass after code changes, ADR capture when a
  decision is made or asked about;
- a `UserPromptSubmit` doc-gate — on implementation-shaped prompts, a one-line
  reminder to read the conventions and a sibling first;
- `mostofi` on PATH — a doc-budget gate measuring markdown in weighted tokens,
  with docstring/comment-block rules and stale-doc scanning.

## Install

```
/plugin marketplace add Behnam-RK/toolshed
/plugin install mostofi@toolshed
```

Needs Python 3.12+: found via `$PYTHON`, `uv python find`, then
`python3.14`…`python3.12`, `python3`.

## CLI

```
mostofi check [files…]       # blocking gate, exit 1 on failure (strict with no files)
mostofi scan [--base REF]    # advisory report, always exit 0
mostofi init [--check]       # scaffold .docs.toml + doc guide + docs/adr/
mostofi --explain RULE       # one rule's reasoning and knobs
```

`bin/docs` is an alias.

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
| `[doc-gate]` `enabled`, `routing_doc`, `trigger` | the prompt hook: on/off, doc it names (`AGENTS.md`), ERE matched per line |
