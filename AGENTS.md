# toolshed

A Claude Code marketplace (`.claude-plugin/marketplace.json`) with two kinds of
plugin under `plugins/`:

- **Upstream** (`mattpocock-skills`, `context-mode`): rebuilt weekly by
  `scripts/sync.sh` from the URLs in `scripts/upstreams`, then
  `patches/<name>.sh`. Never edit them in place; the next sync overwrites
  it. Change the patch script, then run `scripts/sync.sh <name>`.
- **Own** (`mostofi`, `momayez`, `dabir`): edited here. Each plugin's README is its
  user doc; its `skills/*/SKILL.md` is what the agent reads.

## Before changing an own plugin

- Read its README and a sibling file of the same kind (a skill reference, an
  analyzer, a test) and mirror it.
- mostofi's engine is `plugins/mostofi/src/docsteward`. Its tests:
  `uv run --group test pytest`. The doc gate on this repo: `uv run mostofi
  check`, configured by `.docs.toml` (upstream plugins excluded).
- Skill and reference prose is measured by that gate; keep SKILL.md under its
  hard cap and move detail into `references/`.

## Releasing

Bump `plugin.json` `version`; for mostofi also `plugins/mostofi/src/docsteward/__init__.py`
(the `init` pins derive from it) and the `# frozen:` pin in its README. Tag only mostofi, annotated:
`git tag -a mostofi--vX.Y.Z`. pre-commit and uvx pin that tag, so
`plugins/mostofi/skills/mostofi/references/setup.md` resolves its `^{}` commit.
