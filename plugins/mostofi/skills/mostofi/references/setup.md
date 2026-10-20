# Setup

Sets a repo up for mostofi, or reconfigures one that has a `.docs.toml`.
Detect first; ask only what detection can't settle. `.docs.toml` is the
repo's policy; the user's plugin options never write into it.

## 1. Detect

- **Languages**: what `mostofi init` would pick — manifests (`pyproject.toml`,
  `package.json`, `tsconfig.json`, `go.mod`, `Cargo.toml`) and tracked `*.py`/`*.sh`.
- **Convention docs**: an existing documentation guide or code-style doc, and
  a decision log (`docs/adr/`, `docs/decisions/`, `adr/`, `.agents/adr/`…:
  numbered `NNNN-*.md` files, an index README).
- **Routing doc**: the first of `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`.
- **Exclusions**: tracked vendored or generated trees (`vendor/`,
  `third_party/`, `*_generated*`, `gen/`, migrations, snapshots).
- **Gate wiring**: `.pre-commit-config.yaml`, CI workflows.

## 2. Ask

One `AskUserQuestion` round, each option pre-filled from detection:

1. **Profile + languages**: profile defaults to the setup profile from the
   skill's Options; `strict` fails where `default` warns.
2. **Convention docs + ADRs**: write the guide and `docs/adr/`, or reuse what
   exists (its ADR dir, no templates).
3. **Doc-gate**: on or off for this repo, and which routing doc it names.
4. **Exclusions**: which detected trees to skip.

## 3. Write

**Fresh** (no `.docs.toml`): one `mostofi init` call:

```
mostofi init --profile P --lang a,b [--exclude GLOB]… [--adr-dir DIR]
             [--no-guide] [--no-adr] [--doc-gate|--no-doc-gate] [--routing-doc PATH]
```

**Existing**: show the current values, then edit only the keys that change,
in place, keeping comments. Never `--force` over a hand-edited file, and never
touch the ADR index. Then `mostofi init --check`: `missing` for a part the
repo chose not to use is expected; `drift` means its copy differs from the
shipped template, so mention it and leave it.

**Validate** with `mostofi scan`. Exit 2 is a broken config: fix your edit.
Exit 0 is a valid config; its findings are the repo's doc debt, reported
rather than treated as a failed setup.

## 4. Wire the gate

- **pre-commit**: offer to append the hook, and do it only on a yes. Pin the
  tag's sha: `git ls-remote --tags https://github.com/Behnam-RK/toolshed
  'mostofi--v*'`, take the tag `mostofi --version` names (its `^{}` line is
  the commit; the tag is annotated), and write
  `rev: <sha>  # frozen: mostofi--vX.Y.Z`. Offline or not found: `rev:
  mostofi--vX.Y.Z`, and say so. An existing `mostofi` hook: update its `rev`
  only if the user asks.
- **CI**: print, with the version `mostofi --version` names; don't edit workflows:
  `uvx --from 'mostofi[exact] @ git+https://github.com/Behnam-RK/toolshed@mostofi--vX.Y.Z' mostofi check --require-exact`

## 5. Report

```
## Mostofi setup
Config:   .docs.toml — <written|updated: keys> (profile P, langs a,b)
Docs:     <guide/ADR files written, or reused DIR>
Doc-gate: <on|off>, routing <doc>
Gate:     pre-commit <added|already present|declined>; CI snippet printed
Debt:     <n> scan findings — run /mostofi pass to work through them
```
