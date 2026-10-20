# False positives found by running the default config over real repos. Each
# test is the minimal shape of a pattern seen in at least two of them.
import subprocess

from docsteward import config, scanner


def _repo(tmp_path, files):
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'add', '-A'], check=True)
    return tmp_path


def _refs(root, rel):
    text = (root / rel).read_text(encoding='utf-8')
    return scanner.stale_file_refs(root, rel, text, config.load(root))


def test_ref_relative_to_the_docs_own_project(tmp_path):
    # A monorepo service documents its files from its own root, the way its
    # README and tooling name them; no [corpus] package_roots is configured.
    root = _repo(tmp_path, {
        'services/shop/pyproject.toml': '[project]\nname = "shop"\n',
        'services/shop/apps/orders/models.py': '',
        'services/shop/docs/business/orders.md': 'See `apps/orders/models.py`.\n',
    })
    assert _refs(root, 'services/shop/docs/business/orders.md') == []


def test_nested_project_wins_over_its_parent(tmp_path):
    root = _repo(tmp_path, {
        'web/package.json': '{}\n',
        'web/ext/discount/Cargo.toml': '[package]\nname = "d"\n',
        'web/ext/discount/src/run.rs': '',
        'web/ext/discount/corpus/README.md': 'Entry: `src/run.rs`.\n',
    })
    assert _refs(root, 'web/ext/discount/corpus/README.md') == []


def test_a_truly_missing_file_in_a_project_is_still_reported(tmp_path):
    root = _repo(tmp_path, {
        'services/shop/pyproject.toml': '',
        'services/shop/docs/a.md': 'See `apps/gone/models.py`.\n',
    })
    [finding] = _refs(root, 'services/shop/docs/a.md')
    assert 'apps/gone/models.py' in finding.message


def test_an_adr_citing_a_since_removed_file_is_history(tmp_path):
    root = _repo(tmp_path, {
        'docs/adr/0001-single-mode.md': '`docs/modes.md` collapses to one state machine.\n',
    })
    assert _refs(root, 'docs/adr/0001-single-mode.md') == []


def test_an_adr_dir_moved_by_init_keeps_the_exemption(tmp_path):
    from docsteward.cli import main
    root = _repo(tmp_path, {'decisions/0001-x.md': 'Replaced `lib/old.py`.\n'})
    assert main(['init', '--root', str(root), '--no-docs', '--adr-dir', 'decisions']) == 0
    assert _refs(root, 'decisions/0001-x.md') == []


def test_a_repo_can_turn_the_adr_check_back_on(tmp_path):
    root = _repo(tmp_path, {
        '.docs.toml': '[[overrides]]\npattern = "docs/adr/**"\nrules = { stale-file-ref = "warn" }\n',
        'docs/adr/0001-x.md': 'Replaced `lib/old.py`.\n',
    })
    assert len(_refs(root, 'docs/adr/0001-x.md')) == 1
