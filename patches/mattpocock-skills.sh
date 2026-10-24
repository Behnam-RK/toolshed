#!/bin/bash
# Keep only the skills listed below; rename some. Fails loudly if upstream moves a kept skill.
set -euo pipefail
keep=(engineering/ask-matt engineering/tdd engineering/diagnosing-bugs engineering/codebase-design
      engineering/wayfinder engineering/retro engineering/improve-codebase-architecture engineering/triage
      engineering/research engineering/wizard productivity/grilling productivity/grill-me
      productivity/wait-what productivity/teach productivity/to-questionnaire)
renames=(ask-matt:compass diagnosing-bugs:diag to-questionnaire:questionnaire)

for s in "${keep[@]}"; do
  [ -f "skills/$s/SKILL.md" ] || { echo "patch: skills/$s not found upstream" >&2; exit 1; }
done
while IFS= read -r d; do
  printf '%s\n' "${keep[@]}" | grep -qx "${d#skills/}" || rm -rf "$d"
done < <(find skills -name SKILL.md -exec dirname {} \;)
find skills -type d -empty -delete

for r in "${renames[@]}"; do
  old=${r%%:*} new=${r##*:}
  src=$(dirname "$(find skills -path "*/$old/SKILL.md")")
  mv "$src" "$(dirname "$src")/$new"
  # Lookarounds, not captured neighbours: a consumed trailing `/` hid the next `ask-matt/ask-matt`.
  find skills -name '*.md' -exec perl -pi -e "s{(?<![a-z-])\Q$old\E(?![a-z-])}{$new}g" {} +
done

python3 - <<'PY'
import json, pathlib
path = pathlib.Path(".claude-plugin/plugin.json")
d = json.loads(path.read_text())
d["skills"] = sorted(f"./{p.parent}" for p in pathlib.Path("skills").glob("*/*/SKILL.md"))
path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
