import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = load_module("run_skill_evals", ROOT / "scripts" / "run_skill_evals.py")
grader = load_module("grade_skill_evals", ROOT / "scripts" / "grade_skill_evals.py")


class EvalContractTests(unittest.TestCase):
    def test_smoke_suite_has_exact_selected_cases_and_assertions(self):
        cases = runner.load_cases()
        self.assertEqual(18, len(cases))
        self.assertEqual(52, sum(len(case["assertions"]) for case in cases))
        self.assertEqual(
            {(skill, eval_id) for skill, ids in runner.SELECTED.items() for eval_id in ids},
            {(case["skill"], case["eval_id"]) for case in cases},
        )

    def test_checked_in_benchmark_summary_matches_suite(self):
        summary = json.loads((ROOT / "evals" / "results" / "2026-07-17-smoke-summary.json").read_text(encoding="utf-8"))
        cases = runner.load_cases()
        expected = {f"{case['skill']}:{case['eval_id']}" for case in cases}
        self.assertEqual(18, summary["case_count"])
        self.assertEqual(52, summary["assertion_count"])
        self.assertEqual(expected, set(summary["selected_cases"]))
        self.assertEqual(38, summary["initial_benchmark"]["candidate_passed"])
        self.assertEqual(19, summary["initial_benchmark"]["baseline_passed"])
        self.assertEqual(52, summary["revision_benchmark"]["candidate_passed"])
        self.assertEqual(42, summary["revision_benchmark"]["baseline_passed"])

    def test_candidate_and_baseline_keep_task_prompt_identical(self):
        case = runner.load_cases()[0]
        candidate = runner.prompt_for(case, "candidate")
        baseline = runner.prompt_for(case, "baseline")
        marker = "Task prompt (identical across candidate and baseline):\n"
        self.assertEqual(candidate.split(marker, 1)[1], baseline.split(marker, 1)[1])
        self.assertIn("explicitly loaded", candidate)
        self.assertIn("No skill is loaded", baseline)

    def test_every_fixture_configuration_passes_preflight(self):
        with tempfile.TemporaryDirectory(prefix="skill-eval-test-") as temporary:
            root = Path(temporary)
            for case in runner.load_cases():
                for configuration in ("candidate", "baseline"):
                    destination = root / f"{case['skill']}-{case['eval_id']}-{configuration}"
                    primary, cwd = runner.build_fixture(case, destination)
                    if configuration == "candidate":
                        skill = runner.ROOT / case["skill"] / "SKILL.md"
                        runner.write(cwd / ".eval" / "skill" / "SKILL.md", skill.read_text(encoding="utf-8"))
                    result = runner.preflight(case, primary, cwd)
                    self.assertTrue(result["passed"], (case["skill"], case["eval_id"], configuration, result["checks"]))


class GraderTests(unittest.TestCase):
    def test_missing_or_empty_evidence_forces_failure(self):
        expected = ["A", "B", "C"]
        actual = [
            {"text": "A", "passed": True, "evidence": "state/status.txt is clean"},
            {"text": "B", "passed": True, "evidence": ""},
        ]
        results = grader.normalize_results(expected, actual)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])
        self.assertFalse(results[2]["passed"])
        self.assertIn("no concrete evidence", results[1]["evidence"])

    def test_result_order_follows_assertion_contract(self):
        expected = ["first", "second"]
        actual = [
            {"text": "second", "passed": True, "evidence": "e2"},
            {"text": "first", "passed": False, "evidence": "e1"},
        ]
        results = grader.normalize_results(expected, actual)
        self.assertEqual(expected, [item["text"] for item in results])
        self.assertEqual([False, True], [item["passed"] for item in results])


if __name__ == "__main__":
    unittest.main()
