from __future__ import annotations

import sys
from pathlib import Path

from . import __version__
from .config import CONFIG_NAME, DEFAULT_HARD, DEFAULT_SOFT, PROFILES
from .corpus import GitUnavailable, git


TEMPLATES = Path(__file__).resolve().parent / 'templates'

# template file -> where it lands in a consuming repo
DOC_TARGETS = {
    'documentation-guide.md': 'docs/workflows/documentation-guide.md',
    'adr-template.md': 'docs/adr/template.md',
    'adr-README.md': 'docs/adr/README.md',
}

# The ADR index gains a row the moment the repo records a decision, which is the
# scaffold being used as intended. Comparing it byte-for-byte would then report
# drift forever, so it is seeded and never synced.
SEEDED_ONLY = ('adr-README.md',)

LANG_GLOBS = {
    'python': ['*.py'],
    'typescript': ['*.ts', '*.tsx'],
    'javascript': ['*.js', '*.jsx', '*.mjs'],
    'go': ['*.go'],
    'rust': ['*.rs'],
    'shell': ['*.sh'],
}

MARKERS = {
    'pyproject.toml': 'python',
    'setup.py': 'python',
    'tsconfig.json': 'typescript',
    'package.json': 'javascript',
    'go.mod': 'go',
    'Cargo.toml': 'rust',
}

# Found from the files themselves: shell has no manifest, and Python has one
# only sometimes — a manifest-less Python repo reached the default below, which
# one stray `*.sh` was then enough to suppress.
GLOB_MARKERS = {'python': '*.py', 'shell': '*.sh'}

REPO = 'git@github.com:VConvert/ai-toolkit'
GIT_URL = 'git+ssh://git@github.com/VConvert/ai-toolkit'

# A tag names the plugin it releases: `<plugin>--vX.Y.Z`. `docs init` emits pins
# for the docs plugin, because the pre-commit and uvx channels ship only the
# docs gate. See ADR-0004.
PLUGIN = 'docs'


def tag(version: str = __version__) -> str:
    return f'{PLUGIN}--v{version}'


# Tracked files, because that is what the gate will measure: it reaches
# `src/pkg/mod.py` at any depth, and it does not see `node_modules` or a
# virtualenv, which a recursive `rglob` would walk into and be fooled by.
def _has_tracked(root: Path, pattern: str) -> bool:
    try:
        listing = git(root, 'ls-files', '-z', '--', pattern)
    except GitUnavailable:
        # `docs init` is the one command that must work without git: scaffolding
        # a repository is a reasonable thing to do before creating one.
        listing = None
    if listing is not None:
        return any(listing.split('\0'))
    # No index to ask, so probe the root and one level down rather than walking
    # a whole tree that may contain `node_modules` or a virtualenv.
    return any(next(root.glob(p), None) for p in (pattern, f'*/{pattern}'))


def detect_languages(root: Path) -> list[str]:
    found: list[str] = []
    for marker, lang in MARKERS.items():
        if (root / marker).exists() and lang not in found:
            found.append(lang)
    for lang, pattern in GLOB_MARKERS.items():
        if lang not in found and _has_tracked(root, pattern):
            found.append(lang)
    # A TypeScript repo always has a package.json too; the narrower answer wins.
    if 'typescript' in found and 'javascript' in found:
        found.remove('javascript')
    return found or ['python']


def _code_globs(root: Path, lang: str | None) -> list[str]:
    langs = [lang] if lang else detect_languages(root)
    out: list[str] = []
    for name in langs:
        if name not in LANG_GLOBS:
            raise SystemExit(
                f'docs init: unknown --lang {name!r} — choose from '
                f'{", ".join(sorted(LANG_GLOBS))}'
            )
        out += [g for g in LANG_GLOBS[name] if g not in out]
    return out


# Named, and the caps interpolated, so the generated file cannot restate a
# threshold or a rule id that the engine has since changed.
EXAMPLE_RULE = 'docstring'


def _config_text(profile: str, globs: list[str]) -> str:
    rendered = ', '.join(f'"{g}"' for g in globs)
    return f'''# Written by `docs init` v{__version__}. Every key is optional.
# `docs --explain <rule>` prints the reasoning and knobs for one rule.
profile = "{profile}"

[corpus]
code_globs = [{rendered}]

# [defaults]
# soft = {DEFAULT_SOFT}
# hard = {DEFAULT_HARD}

# First match wins; the shipped README and docs/adr/ overrides are consulted last.
# [[overrides]]
# pattern = "docs/legacy/**"
# rules = "off"

# [exclude]
# paths = ["vendor/**"]

# [rules.{EXAMPLE_RULE}]
# severity = "fail"

# [python]
# runtime_surfaced_decorators = ["strawberry", "strawberry_django", "*.tool"]
'''


def _write(
    path: Path, text: str, force: bool, written: list[str], skipped: list[str],
    note: str = '(exists; --force to overwrite)',
):
    if path.exists() and not force:
        skipped.append(f'{path}  {note}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    written.append(str(path))


def _drift(root: Path) -> int:
    drifted = []
    missing = []
    for name, target in DOC_TARGETS.items():
        source = TEMPLATES / name
        landed = root / target
        if not landed.exists():
            missing.append(target)
        elif name in SEEDED_ONLY:
            continue
        elif landed.read_text(encoding='utf-8') != source.read_text(encoding='utf-8'):
            drifted.append(target)
    for target in missing:
        print(f'missing  {target}')
    for target in drifted:
        print(f'drift    {target}  differs from the copy shipped in v{__version__}')
    if not drifted and not missing:
        print(f'all templates match the copies shipped in v{__version__}')
        return 0
    return 1


def init_repo(
    root: Path,
    profile: str = 'default',
    lang: str | None = None,
    force: bool = False,
    write_docs: bool = True,
    drift_check: bool = False,
) -> int:
    if drift_check:
        return _drift(root)
    if profile not in PROFILES:
        print(
            f'docs init: unknown profile {profile!r} — choose from '
            f'{", ".join(sorted(PROFILES))}',
            file=sys.stderr,
        )
        return 2

    written: list[str] = []
    skipped: list[str] = []
    _write(root / CONFIG_NAME, _config_text(profile, _code_globs(root, lang)),
           force, written, skipped)
    if write_docs:
        for name, target in DOC_TARGETS.items():
            # `--force` refreshes the templates, but a seeded file is the repo's
            # own content after the first ADR lands; overwriting it deleted the
            # index that `SEEDED_ONLY` exists to protect from the drift check.
            seeded = name in SEEDED_ONLY
            note = (
                '(seeded once; never overwritten)' if seeded
                else '(exists; --force to overwrite)'
            )
            _write(root / target, (TEMPLATES / name).read_text(encoding='utf-8'),
                   force and not seeded, written, skipped, note)

    for path in written:
        print(f'wrote    {path}')
    for path in skipped:
        print(f'kept     {path}')

    print(f'\nadd to .pre-commit-config.yaml:\n'
          f'  - repo: {REPO}\n'
          f'    rev: {tag()}\n'
          f'    hooks: [{{id: docs}}]\n')
    print(f'add to CI:\n'
          f"  uvx --from 'docsteward[exact] @ {GIT_URL}@{tag()}' "
          f'docs check --require-exact')
    return 0
