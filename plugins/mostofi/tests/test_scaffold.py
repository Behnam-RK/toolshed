import subprocess
import tomllib

import pytest

from docsteward import config, scaffold
from docsteward.cli import main


def _init(root, *flags):
    return main(['init', '--root', str(root), *flags])


def _toml(root):
    return tomllib.loads((root / '.docs.toml').read_text(encoding='utf-8'))


@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    return tmp_path


def test_default_init_writes_config_guide_and_adr(repo):
    assert _init(repo) == 0
    assert (repo / 'docs/workflows/documentation-guide.md').is_file()
    assert (repo / 'docs/adr/template.md').is_file()
    assert (repo / 'docs/adr/README.md').is_file()
    data = _toml(repo)
    assert data['profile'] == 'default'
    # Nothing chosen, so nothing optional is live.
    assert 'exclude' not in data and 'doc-gate' not in data and 'overrides' not in data
    config.load(repo)


def test_every_flag_lands_and_loads(repo):
    assert _init(
        repo, '--profile', 'strict', '--lang', 'python,shell',
        '--exclude', 'vendor/**', '--exclude', 'gen/**',
        '--no-doc-gate', '--routing-doc', 'CLAUDE.md', '--adr-dir', 'decisions/',
    ) == 0
    data = _toml(repo)
    assert data['profile'] == 'strict'
    assert data['corpus']['code_globs'] == ['*.py', '*.sh']
    assert data['exclude']['paths'] == ['vendor/**', 'gen/**']
    assert data['doc-gate'] == {'enabled': False, 'routing_doc': 'CLAUDE.md'}
    assert data['rules']['adr-number-collision'] == {
        'adr_glob': 'decisions/[0-9][0-9][0-9][0-9]-*.md',
        'index': 'decisions/README.md',
    }
    assert data['overrides'] == [
        {'pattern': 'decisions/**', 'soft': 1200, 'hard': 2000, 'structure_rules': False,
         'rules': {'stale-file-ref': 'off'}}
    ]
    loaded = config.load(repo)
    assert loaded.caps_for('decisions/0001-x.md') == (1200, 2000)
    assert (repo / 'decisions/README.md').is_file()
    assert not (repo / 'docs/adr').exists()


def test_doc_gate_on_writes_enabled_true(repo):
    assert _init(repo, '--doc-gate') == 0
    assert _toml(repo)['doc-gate'] == {'enabled': True}


def test_custom_adr_dir_rewrites_guide_paths_and_link(repo):
    assert _init(repo, '--adr-dir', 'decisions') == 0
    guide = (repo / 'docs/workflows/documentation-guide.md').read_text(encoding='utf-8')
    assert 'docs/adr' not in guide
    assert '](../../decisions/README.md)' in guide


def test_drift_check_follows_custom_adr_dir(repo, capsys):
    _init(repo, '--adr-dir', 'decisions')
    capsys.readouterr()
    assert _init(repo, '--check') == 0
    assert 'all templates match' in capsys.readouterr().out


def test_drift_reports_edited_template_and_missing(repo, capsys):
    _init(repo)
    (repo / 'docs/adr/template.md').write_text('mine\n', encoding='utf-8')
    (repo / 'docs/workflows/documentation-guide.md').unlink()
    capsys.readouterr()
    assert _init(repo, '--check') == 1
    out = capsys.readouterr().out
    assert 'drift    docs/adr/template.md' in out
    assert 'missing  docs/workflows/documentation-guide.md' in out


def test_drift_ignores_seeded_index(repo):
    _init(repo)
    (repo / 'docs/adr/README.md').write_text('| ADR-0001 | x |\n', encoding='utf-8')
    assert _init(repo, '--check') == 0


def test_force_never_overwrites_seeded_index(repo):
    _init(repo)
    index = repo / 'docs/adr/README.md'
    index.write_text('ours\n', encoding='utf-8')
    (repo / 'docs/adr/template.md').write_text('stale\n', encoding='utf-8')
    assert _init(repo, '--force') == 0
    assert index.read_text(encoding='utf-8') == 'ours\n'
    assert (repo / 'docs/adr/template.md').read_text(encoding='utf-8') != 'stale\n'


def test_existing_config_is_kept_without_force(repo, capsys):
    (repo / '.docs.toml').write_text('profile = "strict"\n', encoding='utf-8')
    assert _init(repo) == 0
    assert (repo / '.docs.toml').read_text(encoding='utf-8') == 'profile = "strict"\n'
    assert 'kept' in capsys.readouterr().out


def test_no_adr_reusing_a_log_without_index_turns_index_off(repo):
    (repo / 'adr').mkdir()
    (repo / 'adr/0001-x.md').write_text('# x\n', encoding='utf-8')
    assert _init(repo, '--no-adr', '--adr-dir', 'adr') == 0
    assert _toml(repo)['rules']['adr-number-collision']['index'] == ''
    assert not (repo / 'adr/template.md').exists()
    assert (repo / 'docs/workflows/documentation-guide.md').is_file()


def test_no_adr_reusing_a_log_with_index_keeps_it(repo):
    (repo / 'adr').mkdir()
    (repo / 'adr/README.md').write_text('# index\n', encoding='utf-8')
    assert _init(repo, '--no-adr', '--adr-dir', 'adr') == 0
    assert _toml(repo)['rules']['adr-number-collision']['index'] == 'adr/README.md'


def test_no_docs_writes_only_config(repo):
    assert _init(repo, '--no-docs') == 0
    assert sorted(p.name for p in repo.iterdir() if p.name != '.git') == ['.docs.toml']


@pytest.mark.parametrize('bad', ['../elsewhere', '/abs', ''])
def test_adr_dir_outside_repo_is_refused(repo, bad):
    assert _init(repo, '--adr-dir', bad) == 2
    assert not (repo / '.docs.toml').exists()


def test_unknown_profile_writes_nothing(repo):
    assert _init(repo, '--profile', 'nope') == 2
    assert not (repo / '.docs.toml').exists()


def test_config_the_engine_rejects_writes_nothing(repo, monkeypatch):
    monkeypatch.setattr(scaffold, '_config_text', lambda *a: '[nonsense]\n')
    assert _init(repo) == 2
    assert not (repo / '.docs.toml').exists()
    assert not (repo / 'docs').exists()


def test_unknown_lang_is_refused(repo):
    with pytest.raises(SystemExit):
        _init(repo, '--lang', 'cobol')


def test_detect_languages(repo):
    (repo / 'go.mod').write_text('module x\n', encoding='utf-8')
    (repo / 'run.sh').write_text('echo\n', encoding='utf-8')
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    assert scaffold.detect_languages(repo) == ['go', 'shell']


def test_detect_languages_defaults_to_python(tmp_path):
    assert scaffold.detect_languages(tmp_path) == ['python']


def test_pin_output_names_the_release_tag(repo, capsys):
    _init(repo)
    out = capsys.readouterr().out
    assert f'rev: {scaffold.tag()}' in out
    assert f'# frozen: {scaffold.tag()}' in out


def test_guide_links_an_unindexed_reused_log_as_a_directory(repo, capsys):
    # Found by a /mostofi setup dry run: the guide linked a README the reused
    # log never had, so mostofi's own scaffold failed its stale-file-ref rule.
    (repo / 'docs/decisions').mkdir(parents=True)
    (repo / 'docs/decisions/0001-x.md').write_text('# x\n', encoding='utf-8')
    assert _init(repo, '--no-adr', '--adr-dir', 'docs/decisions') == 0
    guide = (repo / 'docs/workflows/documentation-guide.md').read_text(encoding='utf-8')
    assert '](../decisions/)' in guide and 'decisions/README.md' not in guide
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    capsys.readouterr()
    assert main(['scan', '--root', str(repo), '--json']) == 0
    assert 'stale-file-ref' not in capsys.readouterr().out
    assert _init(repo, '--check') == 1
    out = capsys.readouterr().out
    assert 'drift' not in out and 'missing  docs/decisions/template.md' in out


def test_no_adr_without_any_log_writes_no_link(repo, capsys):
    assert _init(repo, '--no-adr') == 0
    guide = (repo / 'docs/workflows/documentation-guide.md').read_text(encoding='utf-8')
    assert '](../adr/' not in guide and '`docs/adr/`' in guide
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    capsys.readouterr()
    assert main(['scan', '--root', str(repo), '--json']) == 0
    assert 'stale-file-ref' not in capsys.readouterr().out
    _init(repo, '--check')
    assert 'drift' not in capsys.readouterr().out


def test_adr_dir_sharing_the_default_prefix_is_named_once(repo):
    assert _init(repo, '--adr-dir', 'docs/adrs') == 0
    guide = (repo / 'docs/workflows/documentation-guide.md').read_text(encoding='utf-8')
    assert '[`docs/adrs/`](../adrs/README.md)' in guide
    assert 'adrss' not in guide
    assert _init(repo, '--check') == 0
