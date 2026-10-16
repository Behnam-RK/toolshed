#!/bin/bash
# Rebuild plugins/<name> from upstream HEAD + patches/<name>.sh, versioned <upstream-version>+<sha7>.
# Usage: scripts/sync.sh [name...]   (default: every entry in scripts/upstreams)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
names=("$@")
[ $# -gt 0 ] || names=($(awk '!/^#/ && NF {print $1}' "$repo/scripts/upstreams"))

for name in "${names[@]}"; do
  read -r _ url excludes < <(awk -v n="$name" '$1 == n' "$repo/scripts/upstreams")
  work=$(mktemp -d)
  git clone --quiet --depth 1 "$url" "$work/src"
  sha=$(git -C "$work/src" rev-parse --short=7 HEAD)
  dest="$repo/plugins/$name"
  rm -rf "$dest" && mkdir -p "$dest"
  rsync -a --exclude .git $(for e in ${excludes//,/ }; do printf -- '--exclude /%s ' "$e"; done) "$work/src/" "$dest/"
  (cd "$dest" && bash "$repo/patches/$name.sh")
  python3 - "$dest/.claude-plugin/plugin.json" "$sha" <<'PY'
import json, sys
path, sha = sys.argv[1:]
d = json.load(open(path))
d["version"] = f"{d.get('version', '0.0.0').split('+')[0]}+{sha}"
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
PY
  echo "$sha" > "$dest/.upstream-sha"
  rm -rf "$work"
  echo "$name -> $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$dest/.claude-plugin/plugin.json")"
done
