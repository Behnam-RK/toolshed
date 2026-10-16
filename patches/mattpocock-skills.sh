#!/bin/bash
# Drop skills that duplicate built-ins or other plugins. Fails loudly if upstream moves them.
set -euo pipefail
drop=(engineering/code-review engineering/pr engineering/domain-modeling engineering/wizard
      engineering/prototype engineering/research)
for s in "${drop[@]}"; do
  [ -d "skills/$s" ] || { echo "patch: skills/$s not found upstream" >&2; exit 1; }
  rm -rf "skills/$s"
done
python3 - "${drop[@]}" <<'PY'
import json, sys
path = ".claude-plugin/plugin.json"
d = json.load(open(path))
gone = {f"./skills/{s}" for s in sys.argv[1:]}
d["skills"] = [s for s in d["skills"] if s not in gone]
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY
