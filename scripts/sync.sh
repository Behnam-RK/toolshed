#!/bin/bash
# Rebuild plugins/<name> from upstream HEAD + patches/<name>.sh, versioned <upstream-version>+<sha7>.
# Usage: scripts/sync.sh [name...]   (default: every entry in scripts/upstreams)
# Built and patched in a temp dir, then copied over plugins/<name>: a failure leaves it as it was.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
names=("$@")
# shellcheck disable=SC2207
[ $# -gt 0 ] || names=($(awk '!/^#/ && NF {print $1}' "$repo/scripts/upstreams"))
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

for name in "${names[@]}"; do
  entry=$(awk -v n="$name" '$1 == n' "$repo/scripts/upstreams")
  [ -n "$entry" ] || { echo "sync: unknown upstream '$name' (not in scripts/upstreams)" >&2; exit 1; }
  [ -f "$repo/patches/$name.sh" ] || { echo "sync: patches/$name.sh is missing" >&2; exit 1; }
  read -r _ url excludes <<<"$entry"
  src="$work/$name/src" build="$work/$name/build"
  git clone --quiet --depth 1 "$url" "$src"
  sha=$(git -C "$src" rev-parse --short=7 HEAD)
  sha="$sha.$(git hash-object "$repo/patches/$name.sh" | cut -c1-6)"  # patch edits ship too
  skip=()
  for e in ${excludes//,/ }; do skip+=(--exclude "/$e"); done
  mkdir -p "$build"
  rsync -a --exclude .git ${skip[@]+"${skip[@]}"} "$src/" "$build/"
  find "$build" -name .gitignore -delete  # upstream ignores its prebuilt bundles; ship them
  (cd "$build" && bash "$repo/patches/$name.sh")
  python3 - "$build/.claude-plugin/plugin.json" "$sha" <<'PY'
import json, sys
path, sha = sys.argv[1:]
d = json.load(open(path))
d["version"] = f"{d.get('version', '0.0.0').split('+')[0]}+{sha}"
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
PY
  echo "${sha%%.*}" > "$build/.upstream-sha"
  dest="$repo/plugins/$name"
  mkdir -p "$dest"
  rsync -a --delete "$build/" "$dest/"
  echo "$name -> $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$dest/.claude-plugin/plugin.json")"
done
