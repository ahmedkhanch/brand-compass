"""Validation evidence must distinguish real failures from checkout path changes."""

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[4] / "ops/validate.py"
spec = importlib.util.spec_from_file_location("delivery_validation", MODULE_PATH)
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


def test_lint_paths_normalize_without_hiding_rule_or_message(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    report = tmp_path / "eslint.json"
    report.write_text(json.dumps([{
        "filePath": str(root / "frontend/page.tsx"),
        "messages": [{"ruleId": "unsafe-change", "severity": 2,
                      "message": f"Failure at {root}/frontend/page.tsx:7"}],
    }]))
    assert validation.lint(report, alias) == [(
        "frontend/page.tsx", "unsafe-change", 2, "Failure at REPOSITORY/frontend/page.tsx:7",
    )]


def test_empty_report_is_not_a_green_test_run(tmp_path):
    report = tmp_path / "pytest.xml"
    report.write_text("<testsuite />")
    with pytest.raises(RuntimeError, match="no cases"):
        validation.tests(report)


def test_test_report_preserves_nonpassing_outcomes(tmp_path):
    report = tmp_path / "pytest.xml"
    report.write_text('''<testsuite>
      <testcase classname="suite" name="ok" />
      <testcase classname="suite" name="bad"><failure message="bad 0x123" /></testcase>
      <testcase classname="suite" name="missing"><skipped message="unavailable" /></testcase>
    </testsuite>''')
    assert validation.tests(report) == {
        ("suite", "ok"): (),
        ("suite", "bad"): (("failure", "bad ADDRESS"),),
        ("suite", "missing"): (("skipped", "unavailable"),),
    }
