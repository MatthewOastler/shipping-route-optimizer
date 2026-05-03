# analysis/conclusion_matrix.py

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd


RANDOM_RESULTS_FILE = "tests/random_route_test_results.csv"
REAL_WORLD_RESULTS_FILE = "tests/real_world_route_test_results.csv"
OUTPUT_FILE = "analysis/conclusion_matrix_results.csv"


def load_results(file_path, test_type):
    if not os.path.exists(file_path):
        return pd.DataFrame([{
            "Test Type": test_type,
            "Check": "File exists",
            "Status": "FAIL",
            "Details": f"Missing file: {file_path}",
        }])

    df = pd.read_csv(file_path)

    return pd.DataFrame([{
        "Test Type": test_type,
        "Check": "File exists",
        "Status": "PASS",
        "Details": f"Loaded {len(df)} rows from {file_path}",
    }])


def evaluate_result_file(file_path, test_type):
    checks = []

    if not os.path.exists(file_path):
        checks.append({
            "Test Type": test_type,
            "Check": "Results file available",
            "Status": "FAIL",
            "Details": f"Missing file: {file_path}",
        })
        return checks

    df = pd.read_csv(file_path)

    total_tests = len(df)
    pass_count = int(df["PASS"].sum()) if "PASS" in df.columns else 0
    fail_count = total_tests - pass_count
    pass_rate = round((pass_count / total_tests) * 100, 2) if total_tests else 0

    checks.append({
        "Test Type": test_type,
        "Check": "All tests passed",
        "Status": "PASS" if fail_count == 0 else "FAIL",
        "Details": f"{pass_count}/{total_tests} passed ({pass_rate}%)",
    })

    if "Cost Match" in df.columns:
        cost_match = bool(df["Cost Match"].all())
        checks.append({
            "Test Type": test_type,
            "Check": "Cost agreement",
            "Status": "PASS" if cost_match else "FAIL",
            "Details": "All algorithm costs match" if cost_match else "Cost mismatch detected",
        })

    if "Route Match" in df.columns:
        route_match = bool(df["Route Match"].all())
        checks.append({
            "Test Type": test_type,
            "Check": "Route agreement",
            "Status": "PASS" if route_match else "WARN",
            "Details": "All algorithm routes match" if route_match else "Costs may match but routes differ",
        })

    if "Error" in df.columns:
        errors = df["Error"].dropna()
        checks.append({
            "Test Type": test_type,
            "Check": "No runtime errors",
            "Status": "PASS" if len(errors) == 0 else "FAIL",
            "Details": f"{len(errors)} error rows found",
        })

    return checks


def build_conclusion_matrix():
    rows = []

    rows.extend(evaluate_result_file(RANDOM_RESULTS_FILE, "Random Route Validation"))
    rows.extend(evaluate_result_file(REAL_WORLD_RESULTS_FILE, "Real-World Route Validation"))

    matrix = pd.DataFrame(rows)

    if matrix.empty:
        final_status = "FAIL"
        final_conclusion = "No validation results available."
    elif (matrix["Status"] == "FAIL").any():
        final_status = "FAIL"
        final_conclusion = "Debug required before release."
    elif (matrix["Status"] == "WARN").any():
        final_status = "WARN"
        final_conclusion = "Mostly trusted, but review route differences."
    else:
        final_status = "PASS"
        final_conclusion = (
            "Validated under current model assumptions. "
            "Algorithms agree and no test failures detected."
        )

    summary = pd.DataFrame([{
        "Test Type": "Overall",
        "Check": "Final conclusion",
        "Status": final_status,
        "Details": final_conclusion,
    }])

    return pd.concat([matrix, summary], ignore_index=True)


if __name__ == "__main__":
    matrix = build_conclusion_matrix()

    print("\n============================================================")
    print("SHIPPING ROUTE OPTIMIZER — CONCLUSION MATRIX")
    print("============================================================\n")

    print(matrix)

    os.makedirs("analysis", exist_ok=True)

    matrix.to_csv(OUTPUT_FILE, index=False)

    print(f"\nConclusion matrix saved to:\n{OUTPUT_FILE}")