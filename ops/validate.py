"""Replay upstream and candidate validation without hiding inherited failures."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

BASE_JOBS = ("backend", "lint", "build")
MEMORY_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")


def run(command, cwd, destination, env):
    with destination.open("w") as output:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
    print(f"{destination.name}: exit {result.returncode}", flush=True)
    return result.returncode


def tests(path):
    cases = {}
    for case in ET.parse(path).iter("testcase"):
        key = (case.get("classname"), case.get("name"))
        failures = [child for child in case if child.tag in {"failure", "error", "skipped"}]
        cases[key] = tuple((child.tag, MEMORY_ADDRESS.sub("ADDRESS", child.get("message", "")))
                           for child in failures)
    if not cases:
        raise RuntimeError("Test report contains no cases")
    return cases


def lint(path, root):
    findings = []
    for item in json.loads(path.read_text()):
        name = str(Path(item["filePath"]).resolve().relative_to(root.resolve()))
        for message in item["messages"]:
            detail = message["message"].replace(str(root.resolve()), "REPOSITORY")
            findings.append((name, message.get("ruleId"), message["severity"], detail))
    return sorted(findings, key=str)


def validate(root, report, python, env, candidate):
    report.mkdir(parents=True)
    env = {**env, "COVERAGE_FILE": str(report / ".coverage"), "COVERAGE_DIR": str(report / "frontend-coverage")}
    backend = [python, "-m", "pytest", "tests", "-q", "--tb=short", f"--junitxml={report / 'pytest.xml'}"]
    if candidate:
        backend += ["--cov=app", f"--cov-report=xml:{report / 'coverage.xml'}", "--cov-report=term-missing"]
    outcomes = {
        "backend": run(backend, root / "backend", report / "backend.log", env),
        "lint": run(["npm", "exec", "--", "eslint", ".", "--format", "json", "--output-file", str(report / "eslint.json")], root / "frontend", report / "lint.log", env),
        "build": run(["npm", "run", "build", "--", "--webpack"], root / "frontend", report / "build.log", env),
    }
    if candidate:
        outcomes["ui-unit"] = run(["npm", "test"], root / "frontend", report / "ui-unit.log", env)
    return outcomes



def source_checks(root, base, reports, python, env):
    changed = subprocess.check_output(["git", "diff", "--name-only", base], cwd=root, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True).splitlines()
    paths = [root / name for name in sorted(set(changed + untracked)) if (root / name).is_file()]
    python_paths = [str(path) for path in paths if path.suffix == ".py"]
    if python_paths and run([python, "-m", "ruff", "check", *python_paths], root, reports / "python-lint.log", env):
        raise RuntimeError("Changed Python files failed lint")
    patch = subprocess.check_output(["git", "diff", "--no-ext-diff", base], cwd=root, text=True)
    additions = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
    for name in untracked:
        path = root / name
        if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".mjs", ".json", ".yml", ".yaml"}:
            additions += "\n" + path.read_text()
    # Detect credential formats without printing a matched value into CI artifacts.
    prefixes = ("sk" + "_live_", "sk" + "-ant-", "gh" + "p_")
    if any(re.search(re.escape(prefix) + r"[A-Za-z0-9_-]{20,}", additions) for prefix in prefixes):
        raise RuntimeError("Possible credential in added source")
    print("Changed-source lint and credential-pattern scan passed", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reports = args.reports.resolve()
    reports.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
           "DEBUG": "false", "DEMO_MODE": "true", "NEXT_TELEMETRY_DISABLED": "1",
           "NEXT_PUBLIC_DEMO_MODE": "1"}
    source_checks(root, args.base, reports, sys.executable, env)
    with tempfile.TemporaryDirectory(prefix="f04-baseline-") as directory:
        baseline = Path(directory) / "source"
        subprocess.run(["git", "worktree", "add", "--detach", str(baseline), args.base], cwd=root, check=True)
        try:
            if run(["npm", "ci"], baseline / "frontend", reports / "baseline-install.log", env):
                raise RuntimeError("Baseline dependency installation failed")
            before = validate(baseline, reports / "baseline", sys.executable, env, False)
            after = validate(root, reports / "candidate", sys.executable, env, True)
            if any(before[job] not in {0, 1} or after[job] not in {0, 1} for job in BASE_JOBS):
                raise RuntimeError("Validation command could not execute")
            original = tests(reports / "baseline/pytest.xml")
            current = tests(reports / "candidate/pytest.xml")
            if any(current.get(key) != value for key, value in original.items()):
                raise RuntimeError("Existing test disappeared or changed result/signature")
            if any(value for key, value in current.items() if key not in original):
                raise RuntimeError("New test is not green")
            if lint(reports / "baseline/eslint.json", baseline) != lint(reports / "candidate/eslint.json", root):
                raise RuntimeError("Frontend lint findings changed")
            if before["build"] or after["build"] or after["ui-unit"]:
                raise RuntimeError("Build or new UI coverage tests failed")
            coverage = run([str(Path(sys.executable).with_name("diff-cover")), str(reports / "candidate/coverage.xml"),
                            f"--compare-branch={args.base}", "--fail-under=100"],
                           root / "backend", reports / "diff-coverage.log", env)
            if coverage:
                raise RuntimeError("Changed Python line coverage is below 100%")
            if run([sys.executable, str(root / "ops/smoke.py"), "--reports", str(reports / "smoke")],
                   root, reports / "smoke.log", env):
                raise RuntimeError("Real HTTP or browser smoke checks failed")
            summary = {"baseline_passed": sum(not value for value in original.values()),
                       "candidate_passed": sum(not value for value in current.values()),
                       "inherited_nonpassing": sum(bool(value) for value in original.values()),
                       "result": "no regression; every new test passes"}
            (reports / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary), flush=True)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(baseline)], cwd=root, check=True)


if __name__ == "__main__":
    main()
