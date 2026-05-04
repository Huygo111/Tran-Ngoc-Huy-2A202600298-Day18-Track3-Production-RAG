"""
Check submission format before submitting.
Run: python check_lab.py

[!] Format errors may prevent automated grading.
"""

import json
import os
import sys
import subprocess


def check_file(path: str, required: bool = True) -> bool:
    if os.path.exists(path):
        print(f"  [v] {path}")
        return True
    elif required:
        print(f"  [x] MISSING: {path}")
        return False
    else:
        print(f"  [!] Optional: {path}")
        return True


def check_json(path: str, required_keys: list[str]) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            print(f"  [x] {path} missing keys: {missing}")
            return False
        print(f"  [v] {path} -- keys OK")
        return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [x] {path} -- {e}")
        return False


def check_todos() -> int:
    """Count remaining TODO markers in src/."""
    count = 0
    for root, _, files in os.walk("src"):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    for line in fh:
                        if "# TODO:" in line:
                            count += 1
    return count


def run_tests() -> tuple[int, int]:
    """Run pytest and return (passed, total)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        lines = result.stdout.strip().split("\n")
        summary = lines[-1] if lines else ""
        # Parse "X passed, Y failed" or "X passed"
        passed = total = 0
        for part in summary.split(","):
            part = part.strip()
            if "passed" in part:
                passed = int(part.split()[0])
                total += passed
            if "failed" in part:
                total += int(part.split()[0])
        return passed, total
    except Exception as e:
        print(f"  [!] pytest error: {e}")
        return 0, 0


def validate():
    print("Checking Lab 18 submission: Production RAG\n")
    errors = 0

    # 1. Source files
    print("Source code:")
    for f in ["src/m1_chunking.py", "src/m2_search.py", "src/m3_rerank.py",
              "src/m4_eval.py", "src/pipeline.py"]:
        if not check_file(f):
            errors += 1

    # 2. Reports
    print("\nReports:")
    if check_file("reports/ragas_report.json"):
        if not check_json("reports/ragas_report.json", ["aggregate", "num_questions"]):
            errors += 1
    else:
        errors += 1
    check_file("reports/naive_baseline_report.json", required=False)

    # 3. Analysis
    print("\nAnalysis:")
    check_file("analysis/failure_analysis.md")
    check_file("analysis/group_report.md")

    # 4. Individual reflections
    print("\nIndividual reflections:")
    reflections = []
    ref_dir = "analysis/reflections"
    if os.path.isdir(ref_dir):
        reflections = [f for f in os.listdir(ref_dir) if f.startswith("reflection_") and f.endswith(".md")]
    if reflections:
        for r in reflections:
            print(f"  [v] {ref_dir}/{r}")
    else:
        print(f"  [!] No individual reflection file in {ref_dir}/")

    # 5. TODO count
    print("\nTODO markers:")
    todo_count = check_todos()
    if todo_count == 0:
        print("  [v] No TODOs remaining")
    else:
        print(f"  [!] {todo_count} TODOs remaining")

    # 6. Tests
    print("\nAuto-tests:")
    passed, total = run_tests()
    if total > 0:
        pct = passed / total * 100
        print(f"  {'[v]' if pct >= 80 else '[!]'} {passed}/{total} tests passed ({pct:.0f}%)")
    else:
        print("  [!] Could not run tests")

    # 7. Summary
    print("\n" + "=" * 50)
    if errors == 0:
        print("READY TO SUBMIT!")
    else:
        print(f"FAILED: {errors} errors. Fix before submitting.")
    print("=" * 50)


if __name__ == "__main__":
    validate()
