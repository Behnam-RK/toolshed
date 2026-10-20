from __future__ import annotations

import json
import sys

import pytest
from helpers import git, repo, write

from docsteward.cli import main


DOCSTRING = 'def f():\n    """Doc."""\n'


@pytest.fixture(autouse=True)
def estimate(monkeypatch, tmp_path):
    monkeypatch.setenv('DOCS_COUNTER', 'estimate')
    monkeypatch.setenv('TIKTOKEN_CACHE_DIR', str(tmp_path / 'tiktoken'))
    for name in ('DOCS_ROOT', 'DOC_BUDGET_ROOT'):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def clean(tmp_path):
    return repo(tmp_path, {'README.md': '# Project\n\nShort.\n', 'app.py': 'x = 1\n'})


def run(root, *args):
    return main([*args, '--root', str(root)])


def report(capsys):
    return json.loads(capsys.readouterr().out)


def repo_add(root):
    git(root, 'add', '-A')


# --- check --------------------------------------------------------------------


def test_check_clean_repo(clean, capsys):
    assert run(clean, 'check') == 0
    out = capsys.readouterr().out
    assert '0 failures' in out
    assert 'ESTIMATED' in out


def test_check_fails_on_a_docstring_under_strict(clean, capsys):
    write(clean, {'app.py': DOCSTRING})
    assert run(clean, 'check', '--profile', 'strict') == 1
    err = capsys.readouterr().err
    assert 'FAIL  app.py:1' in err
    assert '1 failure(s)' in err


def test_check_fails_on_the_hard_cap(clean, capsys):
    write(clean, {
        '.docs.toml': '[defaults]\nsoft = 5\nhard = 10\n',
        'docs/big.md': '# Big\n\n' + 'word ' * 20 + '\n',
    })
    repo_add(clean)
    assert run(clean, 'check') == 1
    assert 'FAIL  docs/big.md\n' in capsys.readouterr().err


def test_check_warnings_alone_exit_0(clean, capsys):
    write(clean, {'docs/long.md': '# Long\n\n' + 'word ' * 30 + '\n'})
    repo_add(clean)
    assert run(clean, 'check') == 0
    out = capsys.readouterr().out
    assert 'prose-line-long' in out
    assert '--verbose' in out


def test_check_verbose_lists_warnings(clean, capsys):
    write(clean, {'docs/long.md': '# Long\n\n' + 'word ' * 30 + '\n'})
    repo_add(clean)
    assert run(clean, 'check', '--verbose') == 0
    assert 'WARN  docs/long.md:3' in capsys.readouterr().out


def test_check_untracked_files_are_not_measured(clean, capsys):
    write(clean, {'app.py': 'x = 1\n', 'new.py': DOCSTRING})
    assert run(clean, 'check', '--profile', 'strict') == 0


def test_check_scoped_to_files(clean, capsys):
    write(clean, {'other.py': DOCSTRING})
    repo_add(clean)
    assert run(clean, 'check', '--profile', 'strict', 'app.py') == 0
    assert run(clean, 'check', '--profile', 'strict', 'other.py') == 1


def test_check_require_exact_without_tiktoken_exits_2(clean, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, 'tiktoken', None)
    assert run(clean, 'check', '--require-exact') == 2
    assert 'exact token counts required' in capsys.readouterr().err


def test_check_outside_a_git_repo_exits_2(tmp_path, capsys):
    assert run(tmp_path, 'check') == 2
    assert 'not a git repository' in capsys.readouterr().err


# --- scan ---------------------------------------------------------------------


def test_scan_exits_0_with_findings(clean, capsys):
    write(clean, {'app.py': DOCSTRING})
    assert run(clean, 'scan', '--profile', 'strict', '--json') == 0
    [finding] = report(capsys)['findings']
    assert (finding['rule'], finding['severity']) == ('docstring', 'warn')


def test_scan_reports_rules_that_are_off_by_default(clean, capsys):
    write(clean, {'app.py': DOCSTRING})
    assert run(clean, 'check', '--json') == 0
    assert report(capsys)['findings'] == []
    assert run(clean, 'scan', '--json') == 0
    assert [f['rule'] for f in report(capsys)['findings']] == ['docstring']


def test_scan_respects_a_stated_off(clean, capsys):
    write(clean, {'app.py': DOCSTRING, '.docs.toml': '[rules.docstring]\nseverity = "off"\n'})
    assert run(clean, 'scan', '--json') == 0
    assert report(capsys)['findings'] == []


# --- config errors ------------------------------------------------------------


@pytest.mark.parametrize('command', ['check', 'scan'])
def test_config_error_exits_2(clean, capsys, command):
    write(clean, {'.docs.toml': '[exclude]\npaths = "vendor"\n'})
    assert run(clean, command) == 2
    assert capsys.readouterr().err.startswith('mostofi: [exclude]: paths must be')


def test_unknown_profile_flag_exits_2(clean, capsys):
    assert run(clean, 'check', '--profile', 'nope') == 2
    assert 'unknown profile' in capsys.readouterr().err


def test_explicit_config_path(clean, capsys):
    write(clean, {'app.py': DOCSTRING, 'alt.toml': 'profile = "strict"\n'})
    assert run(clean, 'check', '--config', str(clean / 'alt.toml')) == 1
    assert run(clean, 'check', '--config', str(clean / 'missing.toml')) == 2


# --- explain and help ---------------------------------------------------------


def test_explain_a_rule(capsys):
    assert main(['--explain', 'wall-of-text']) == 0
    out = capsys.readouterr().out
    assert out.startswith('wall-of-text  (default severity: warn)')
    assert 'tokens_per_heading = 450' in out
    assert '[rules.wall-of-text]' in out


def test_explain_a_rule_without_knobs(capsys):
    assert main(['--explain', 'docstring']) == 0
    assert 'knobs' not in capsys.readouterr().out


def test_explain_unknown_rule_exits_2(capsys):
    assert main(['--explain', 'nope']) == 2
    err = capsys.readouterr().err
    assert "unknown rule 'nope'" in err
    assert 'wall-of-text' in err


def test_no_command_prints_help_and_exits_2(capsys):
    assert main([]) == 2
    assert 'usage: mostofi' in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['--version'])
    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith('mostofi ')


# --- json ---------------------------------------------------------------------


def test_json_shape(clean, capsys):
    write(clean, {'CHANGELOG.md': '# Log\n'})
    repo_add(clean)
    assert run(clean, 'check', '--json') == 0
    data = report(capsys)
    assert data['counter'] == 'estimate'
    assert data['exact'] is False
    assert data['caps'] == {'soft': 1000, 'hard': 1400, 'readme_soft': 2000, 'readme_hard': 3000}
    assert data['exempt'] == ['CHANGELOG.md (pattern)']
    assert [d['rel'] for d in data['docs']] == ['README.md']
    assert data['docs'][0]['sections'] == 1


def test_json_finding_fields(clean, capsys):
    write(clean, {'app.py': DOCSTRING})
    assert run(clean, 'check', '--profile', 'strict', '--json') == 1
    [finding] = report(capsys)['findings']
    assert finding == {
        'rel': 'app.py', 'line': 1, 'rule': 'docstring', 'severity': 'fail',
        'message': 'f has a docstring — not runtime-surfaced, delete', 'hint': '',
    }


def test_exempt_marker_is_listed(clean, capsys):
    write(clean, {'docs/gen.md': '<!-- docs: exempt — generated -->\n' + 'word ' * 3000})
    repo_add(clean)
    assert run(clean, 'check', '--json') == 0
    assert report(capsys)['exempt'] == ['docs/gen.md (marker: generated)']
