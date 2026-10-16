#!/bin/bash
# Keep the ctx_* MCP tools and session memory; caveman owns output condensing, so drop
# the tool-rewriting PreToolUse hooks, the SessionStart routing block and the ctx-* skills.
set -euo pipefail
python3 <<'PY'
import json
path = "hooks/hooks.json"
d = json.load(open(path))
d["hooks"].pop("PreToolUse")
json.dump(d, open(path, "w"), indent=2)

path = ".claude-plugin/plugin.json"
d = json.load(open(path))
d.pop("skills")
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY
rm -rf skills

old='let additionalContext = ROUTING_BLOCK;'
grep -qF "$old" hooks/sessionstart.mjs || { echo "patch: routing block line moved upstream" >&2; exit 1; }
sed -i.bak "s/$old/let additionalContext = \"\";/" hooks/sessionstart.mjs && rm hooks/sessionstart.mjs.bak
