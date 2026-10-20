from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path, PurePosixPath

from . import __version__
from .config import (
    BUILTIN_OVERRIDES, CONFIG_NAME, DEFAULT_HARD, DEFAULT_SOFT, PROFILES, RULE_DEFAULTS,
    Config, ConfigError, load as load_config,
)
from .corpus import GitUnavailable, git


TEMPLATES = Path(__file__).resolve().parent / 'templates'

GUIDE = 'documentation-guide.md'
GUIDE_TARGET = 'docs/workflows/documentation-guide.md'
# template file -> its name inside the repo's ADR directory
ADR_FILES = {'adr-template.md': 'template.md', 'adr-README.md': 'README.md'}

ADR_RULE = 'adr-number-collision'
# Where the shipped config expects the decision log, read off the rule that
# polices it so the two cannot disagree.
DEFAULT_ADR_DIR = str(PurePosixPath(RULE_DEFAULTS[ADR_RULE]['index']).parent)
ADR_NAME_GLOB = PurePosixPath(RULE_DEFAULTS[ADR_RULE]['adr_glob']).name

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

REPO = 'https://github.com/Behnam-RK/toolshed'
GIT_URL = 'git+https://github.com/Behnam-RK/toolshed'

# A tag names the plugin it releases: `<plugin>--vX.Y.Z`. `mostofi init` emits
# pins for mostofi, the one plugin the pre-commit and uvx channels ship.
PLUGIN = 'mostofi'


def tag(version: str = __version__) -> str:
    return f'{PLUGIN}--v{version}'


# Tracked files, because that is what the gate will measure: it reaches
# `src/pkg/mod.py` at any depth, and it does not see `node_modules` or a
# virtualenv, which a recursive `rglob` would walk into and be fooled by.
def _has_tracked(root: Path, pattern: str) -> bool:
    try:
        listing = git(root, 'ls-files', '-z', '--', pattern)
    except GitUnavailable:
        # `mostofi init` is the one command that must work without git: scaffolding
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
    langs = [name.strip() for name in lang.split(',') if name.strip()] if lang else []
    langs = langs or detect_languages(root)
    out: list[str] = []
    for name in langs:
        if name not in LANG_GLOBS:
            raise SystemExit(
                f'mostofi init: unknown --lang {name!r} — choose from '
                f'{", ".join(sorted(LANG_GLOBS))}'
            )
        out += [g for g in LANG_GLOBS[name] if g not in out]
    return out


def _adr_override(adr_dir: str) -> dict:
    # The shipped `docs/adr/**` caps, moved: an ADR elsewhere is still a record
    # of a past decision, and trimming one to fit a budget rewrites history.
    shipped = next(o for o in BUILTIN_OVERRIDES if o['pattern'] == f'{DEFAULT_ADR_DIR}/**')
    return {**shipped, 'pattern': f'{adr_dir}/**'}


def _toml(value) -> str:
    # JSON's string, number and array syntax is valid TOML; its objects are not.
    if isinstance(value, dict):
        return '{ ' + ', '.join(f'{_toml(k)} = {_toml(v)}' for k, v in value.items()) + ' }'
    return json.dumps(value, ensure_ascii=False)


# Named, and the caps interpolated, so the generated file cannot restate a
# threshold or a rule id that the engine has since changed.
EXAMPLE_RULE = 'docstring'


def _config_text(
    profile: str,
    globs: list[str],
    exclude: list[str] | None = None,
    doc_gate: bool | None = None,
    routing_doc: str | None = None,
    adr_dir: str = DEFAULT_ADR_DIR,
    adr_index: str | None = None,
) -> str:
    # What the caller chose is written live; the rest stays a commented example.
    parts = [
        f'# Written by `mostofi init` v{__version__}. Every key is optional.\n'
        f'# `mostofi --explain <rule>` prints the reasoning and knobs for one rule.\n'
        f'profile = {_toml(profile)}\n'
        f'\n[corpus]\ncode_globs = [{", ".join(_toml(g) for g in globs)}]\n'
        f'\n# [defaults]\n# soft = {DEFAULT_SOFT}\n# hard = {DEFAULT_HARD}\n'
        f'\n# First match wins; the shipped README and {DEFAULT_ADR_DIR}/ overrides are consulted last.\n'
    ]
    if adr_dir != DEFAULT_ADR_DIR:
        override = _adr_override(adr_dir)
        parts.append(
            '[[overrides]]\n'
            + ''.join(f'{key} = {_toml(value)}\n' for key, value in override.items())
        )
    else:
        parts.append('# [[overrides]]\n# pattern = "docs/legacy/**"\n# rules = "off"\n')

    if exclude:
        parts.append(f'\n[exclude]\npaths = [{", ".join(_toml(p) for p in exclude)}]\n')
    else:
        parts.append('\n# [exclude]\n# paths = ["vendor/**"]\n')

    if adr_dir != DEFAULT_ADR_DIR or adr_index is not None:
        index = f'{adr_dir}/README.md' if adr_index is None else adr_index
        parts.append(
            f'\n[rules.{ADR_RULE}]\n'
            f'adr_glob = {_toml(f"{adr_dir}/{ADR_NAME_GLOB}")}\n'
            f'index = {_toml(index)}\n'
        )
    parts.append(f'\n# [rules.{EXAMPLE_RULE}]\n# severity = "fail"\n')
    parts.append(
        '\n# [python]\n'
        '# runtime_surfaced_decorators = ["strawberry", "strawberry_django", "*.tool"]\n'
    )

    if doc_gate is not None or routing_doc:
        gate = '\n[doc-gate]\n'
        if doc_gate is not None:
            gate += f'enabled = {"true" if doc_gate else "false"}\n'
        if routing_doc:
            gate += f'routing_doc = {_toml(routing_doc)}\n'
        parts.append(gate)
    return ''.join(parts)


def _template(name: str, adr_dir: str) -> str:
    text = (TEMPLATES / name).read_text(encoding='utf-8')
    if name != GUIDE or adr_dir == DEFAULT_ADR_DIR:
        return text
    # The guide names the decision log by path and links its index relative to
    # where the guide lands; both follow the directory the repo chose.
    shipped_link = os.path.relpath(f'{DEFAULT_ADR_DIR}/README.md', PurePosixPath(GUIDE_TARGET).parent)
    link = os.path.relpath(f'{adr_dir}/README.md', PurePosixPath(GUIDE_TARGET).parent)
    return text.replace(f']({shipped_link})', f']({link})').replace(DEFAULT_ADR_DIR, adr_dir)


def _targets(adr_dir: str, guide: bool = True, adr: bool = True) -> dict[str, str]:
    out = {GUIDE: GUIDE_TARGET} if guide else {}
    if adr:
        out.update({name: f'{adr_dir}/{landed}' for name, landed in ADR_FILES.items()})
    return out


def _repo_adr_dir(root: Path) -> str:
    # The drift check has no flags to say where the log went, but the config the
    # same init wrote does; a broken or absent one means the shipped place.
    try:
        glob = load_config(root).rule(ADR_RULE).opts['adr_glob']
    except (ConfigError, OSError):
        return DEFAULT_ADR_DIR
    return str(PurePosixPath(glob).parent)


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
    adr_dir = _repo_adr_dir(root)
    drifted = []
    missing = []
    for name, target in _targets(adr_dir).items():
        landed = root / target
        if not landed.exists():
            missing.append(target)
        elif name in SEEDED_ONLY:
            continue
        elif landed.read_text(encoding='utf-8') != _template(name, adr_dir):
            drifted.append(target)
    for target in missing:
        print(f'missing  {target}')
    for target in drifted:
        print(f'drift    {target}  differs from the copy shipped in v{__version__}')
    if not drifted and not missing:
        print(f'all templates match the copies shipped in v{__version__}')
        return 0
    return 1


def _relative_dir(value: str) -> str | None:
    path = PurePosixPath(value.strip().rstrip('/'))
    if not value.strip() or path.is_absolute() or '..' in path.parts:
        return None
    return str(path)


def init_repo(
    root: Path,
    profile: str = 'default',
    lang: str | None = None,
    force: bool = False,
    write_guide: bool = True,
    write_adr: bool = True,
    drift_check: bool = False,
    exclude: list[str] | None = None,
    doc_gate: bool | None = None,
    routing_doc: str | None = None,
    adr_dir: str = DEFAULT_ADR_DIR,
) -> int:
    if drift_check:
        return _drift(root)
    if profile not in PROFILES:
        print(
            f'mostofi init: unknown profile {profile!r} — choose from '
            f'{", ".join(sorted(PROFILES))}',
            file=sys.stderr,
        )
        return 2
    chosen = _relative_dir(adr_dir)
    if chosen is None:
        print(f'mostofi init: --adr-dir {adr_dir!r} must be a path inside the repo',
              file=sys.stderr)
        return 2

    # A decision log the repo already keeps elsewhere may have no index; pointing
    # the rule at a missing README would report every ADR as unindexed.
    adr_index = None
    if not write_adr and not (root / chosen / 'README.md').exists():
        adr_index = ''
    text = _config_text(profile, _code_globs(root, lang), exclude, doc_gate, routing_doc,
                        chosen, adr_index)
    # Checked against the engine before anything lands: a flag value the
    # validator rejects would otherwise leave a config every later run refuses.
    try:
        Config(tomllib.loads(text))
    except (ConfigError, tomllib.TOMLDecodeError) as exc:
        print(f'mostofi init: the generated config is invalid — {exc}', file=sys.stderr)
        return 2

    written: list[str] = []
    skipped: list[str] = []
    _write(root / CONFIG_NAME, text, force, written, skipped)
    for name, target in _targets(chosen, write_guide, write_adr).items():
        # `--force` refreshes the templates, but a seeded file is the repo's
        # own content after the first ADR lands; overwriting it deleted the
        # index that `SEEDED_ONLY` exists to protect from the drift check.
        seeded = name in SEEDED_ONLY
        note = (
            '(seeded once; never overwritten)' if seeded
            else '(exists; --force to overwrite)'
        )
        _write(root / target, _template(name, chosen),
               force and not seeded, written, skipped, note)

    for path in written:
        print(f'wrote    {path}')
    for path in skipped:
        print(f'kept     {path}')

    print(f'\nadd to .pre-commit-config.yaml (prefer the tag\'s sha: '
          f'rev: <sha>  # frozen: {tag()}):\n'
          f'  - repo: {REPO}\n'
          f'    rev: {tag()}\n'
          f'    hooks: [{{id: mostofi}}]\n')
    print(f'add to CI:\n'
          f"  uvx --from 'mostofi[exact] @ {GIT_URL}@{tag()}' "
          f'mostofi check --require-exact')
    return 0
