from __future__ import annotations

import json

import pytest
from helpers import commit, git, repo, rules

from docsteward import cli, scanner
from docsteward.config import WARN, Config
from docsteward.corpus import GitUnavailable


ON = rules(changed_without_docs='warn')


@pytest.fixture
def base(tmp_path):
    repo(tmp_path)
    return commit(tmp_path, {'app.py': 'x = 1\n', 'README.md': '# App\n', 'CHANGELOG.md': '# Log\n'})


def changed(tmp_path, base, config=ON):
    return scanner.changed_without_docs(tmp_path, base, config)


def test_code_without_docs(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n', 'lib.py': 'y = 1\n'})
    [finding] = changed(tmp_path, base)
    assert finding.rule == 'changed-without-docs'
    assert finding.rel == '.'
    assert finding.severity == WARN
    assert finding.message == f'2 file(s) changed since {base}, no doc changed'


def test_code_with_docs(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n', 'README.md': '# App, changed\n'})
    assert changed(tmp_path, base) == []


def test_docs_only(tmp_path, base):
    commit(tmp_path, {'README.md': '# App, changed\n'})
    assert changed(tmp_path, base) == []


def test_changelog_alone_is_not_a_doc_change(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n', 'CHANGELOG.md': '# Log\n\n- x\n'})
    assert len(changed(tmp_path, base)) == 1


def test_excluded_and_muted_code_needs_no_doc(tmp_path, base):
    commit(tmp_path, {'vendor/a.py': 'v = 1\n', 'gen/b.py': 'g = 1\n'})
    cfg = Config({
        'rules': {'changed-without-docs': {'severity': 'warn'}},
        'exclude': {'paths': ['vendor/**']},
        'overrides': [{'pattern': 'gen/**', 'rules': 'off'}],
    })
    assert changed(tmp_path, base, cfg) == []


def test_a_muted_doc_does_not_count_as_a_doc_change(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n', 'gen/notes.md': '# generated\n'})
    cfg = Config({
        'rules': {'changed-without-docs': {'severity': 'warn'}},
        'overrides': [{'pattern': 'gen/**', 'rules': 'off'}],
    })
    assert len(changed(tmp_path, base, cfg)) == 1


def test_off_by_default_and_without_a_base(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n'})
    assert changed(tmp_path, base, Config()) == []
    assert changed(tmp_path, None) == []


def test_scan_view_turns_it_on(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n'})
    assert len(changed(tmp_path, base, Config().for_scan())) == 1


def test_stated_off_stays_off_in_a_scan(tmp_path, base):
    commit(tmp_path, {'app.py': 'x = 2\n'})
    assert changed(tmp_path, base, rules(changed_without_docs='off').for_scan()) == []


def test_unresolvable_base_is_an_error(tmp_path, base):
    with pytest.raises(GitUnavailable, match='cannot resolve --base'):
        changed(tmp_path, 'no-such-ref')


def test_root_inside_a_repo_sees_only_its_subtree(tmp_path):
    repo(tmp_path)
    first = commit(tmp_path, {'svc/app.py': 'x = 1\n', 'other/lib.py': 'y = 1\n'})
    commit(tmp_path, {'other/lib.py': 'y = 2\n'})
    assert changed(tmp_path / 'svc', first) == []
    assert len(changed(tmp_path, first)) == 1


def test_custom_code_globs(tmp_path, base):
    commit(tmp_path, {'main.go': 'package main\n'})
    assert changed(tmp_path, base) == []
    cfg = Config({'rules': {'changed-without-docs': {'severity': 'warn'}},
                  'corpus': {'code_globs': ['*.go']}})
    assert len(changed(tmp_path, base, cfg)) == 1


# --- through the CLI ----------------------------------------------------------


@pytest.fixture
def estimate(monkeypatch, tmp_path):
    monkeypatch.setenv('DOCS_COUNTER', 'estimate')
    monkeypatch.setenv('TIKTOKEN_CACHE_DIR', str(tmp_path / 'tiktoken'))


def scan_json(root, *args):
    return cli.main(['scan', '--root', str(root), '--json', *args])


def test_scan_base_reports_changed_without_docs(tmp_path, base, estimate, capsys):
    commit(tmp_path, {'app.py': 'x = 2\n'})
    assert scan_json(tmp_path, '--base', base) == 0
    report = json.loads(capsys.readouterr().out)
    assert [f['rule'] for f in report['findings']] == ['changed-without-docs']


def test_scan_without_base_does_not_report_it(tmp_path, base, estimate, capsys):
    commit(tmp_path, {'app.py': 'x = 2\n'})
    assert scan_json(tmp_path) == 0
    assert json.loads(capsys.readouterr().out)['findings'] == []


def test_scan_bad_base_exits_2(tmp_path, base, estimate, capsys):
    assert scan_json(tmp_path, '--base', 'nope') == 2
    assert 'cannot resolve --base' in capsys.readouterr().err


# --- suffix index -------------------------------------------------------------


def test_suffix_index(tmp_path):
    repo(tmp_path, {'a/b/c.py': ''})
    index = scanner.suffix_index(tmp_path)
    assert {'a/b/c.py', 'b/c.py', 'c.py', 'a', 'a/b', 'b'} <= index
    assert 'a/c.py' not in index


def test_resolve_by_suffix_through_the_cli(tmp_path, estimate, capsys):
    repo(tmp_path, {'pkg/src/mod.py': 'x = 1\n', 'README.md': '# R\n\nsee `src/mod.py`\n'})
    assert scan_json(tmp_path) == 0
    assert [f['rule'] for f in json.loads(capsys.readouterr().out)['findings']] == ['stale-file-ref']
    (tmp_path / '.docs.toml').write_text('[rules.stale-file-ref]\nresolve_by_suffix = true\n')
    git(tmp_path, 'add', '.docs.toml')
    assert scan_json(tmp_path) == 0
    assert json.loads(capsys.readouterr().out)['findings'] == []
