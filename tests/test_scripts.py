"""Tests for the business-hq scripts. Run from the repo root:

    python3 -m unittest discover tests -v

The spreadsheet check recalculates model.xlsx in LibreOffice and compares every
line to the Python calculation; it is skipped if LibreOffice isn't installed.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "business-hq"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import financial_model as fm  # noqa: E402
import market_size as ms  # noqa: E402
import scorecard as sc  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def scores(**overrides):
    base = {d: {"score": 4, "evidence": "medium"} for d in sc.DIMENSIONS}
    for k, v in overrides.items():
        base[k] = v
    return {"idea": "test", "scores": base}


class Scorecard(unittest.TestCase):
    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(w for w, _, _ in sc.DIMENSIONS.values()), 1.0)

    def test_build(self):
        self.assertEqual(sc.evaluate(scores())["verdict"], "BUILD")

    def test_critical_one_kills(self):
        r = sc.evaluate(scores(willingness_to_pay={"score": 1, "evidence": "medium"}))
        self.assertEqual(r["verdict"], "KILL")

    def test_critical_two_pivots(self):
        r = sc.evaluate(scores(distribution_access={"score": 2, "evidence": "medium"}))
        self.assertEqual(r["verdict"], "PIVOT")

    def test_weak_critical_evidence_means_test_first(self):
        r = sc.evaluate(scores(problem_severity={"score": 5, "evidence": "weak"}))
        self.assertEqual(r["verdict"], "TEST FIRST")

    def test_low_average_kills(self):
        r = sc.evaluate({"idea": "x", "scores": {d: {"score": 2, "evidence": "medium"} for d in sc.DIMENSIONS}})
        self.assertEqual(r["verdict"], "KILL")

    def test_missing_dimension_errors(self):
        d = scores()
        del d["scores"]["feasibility"]
        with self.assertRaises(ValueError):
            sc.evaluate(d)

    def test_bad_score_errors(self):
        with self.assertRaises(ValueError):
            sc.evaluate(scores(feasibility={"score": 6, "evidence": "medium"}))

    def test_example_file_runs(self):
        p = run(str(SCRIPTS / "scorecard.py"), str(SKILL / "examples" / "scorecard.example.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Verdict:", p.stdout)


class MarketSize(unittest.TestCase):
    def test_bottom_up_maths(self):
        r = ms.size({"segments": [{"name": "a", "customers": 1000, "annual_value": 100,
                                   "serviceable_pct": 0.5, "obtainable_pct_year3": 0.04, "source": "s"}]})
        self.assertAlmostEqual(r["tam"], 100_000)
        self.assertAlmostEqual(r["sam"], 50_000)
        self.assertAlmostEqual(r["som"], 2_000)
        self.assertAlmostEqual(r["som_customers"], 20)
        self.assertEqual(r["flags"], [])

    def test_flags(self):
        r = ms.size({"segments": [{"name": "a", "customers": 1000, "annual_value": 100,
                                   "serviceable_pct": 0.9, "obtainable_pct_year3": 0.2}],
                     "top_down": {"total_market_value": 10_000_000, "relevant_pct": 1},
                     "capacity_check": {"max_new_customers_per_month": 1, "months": 12}})
        text = " ".join(r["flags"])
        for needle in ("no source", "aggressive", "serviceable share", "differ by", "capped by distribution"):
            self.assertIn(needle, text)

    def test_example_file_runs(self):
        p = run(str(SCRIPTS / "market_size.py"), str(SKILL / "examples" / "market_size.example.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SOM", p.stdout)


class UnitEconomics(unittest.TestCase):
    def ue(self, *args):
        p = run(str(SCRIPTS / "unit_economics.py"), *args, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_subscription(self):
        r = self.ue("--model", "subscription", "--price", "10", "--gross-margin", "0.8",
                    "--churn", "0.05", "--cac", "40")
        self.assertAlmostEqual(r["ltv"], 160)          # 10 * 0.8 * 20 months
        self.assertAlmostEqual(r["ltv_to_cac"], 4)
        self.assertAlmostEqual(r["payback_months"], 5)

    def test_lifetime_cap(self):
        r = self.ue("--model", "subscription", "--price", "10", "--gross-margin", "1",
                    "--churn", "0.001", "--cac", "10")
        self.assertEqual(r["expected_lifetime_months"], 60)

    def test_transactional(self):
        r = self.ue("--model", "transactional", "--price", "50", "--gross-margin", "0.4",
                    "--orders-per-year", "2", "--lifetime-years", "3",
                    "--marketing-spend", "300", "--new-customers", "10")
        self.assertAlmostEqual(r["cac"], 30)
        self.assertAlmostEqual(r["ltv"], 120)          # 20 * 6 orders
        self.assertAlmostEqual(r["orders_to_payback"], 1.5)
        self.assertAlmostEqual(r["payback_months"], 9)

    def test_losing_money_flag(self):
        r = self.ue("--model", "subscription", "--price", "5", "--gross-margin", "0.5",
                    "--churn", "0.2", "--cac", "100")
        self.assertTrue(any("loses money" in f for f in r["flags"]))


class FinancialModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.a = fm.normalise(fm.TEMPLATE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cash_identity(self):
        s = fm.simulate(self.a)
        L = s["lines"]
        start = self.a["starting_cash"]
        total = sum(L["Net profit"]) + sum(L["Funding received"]) - sum(L["Startup costs"])
        self.assertAlmostEqual(L["Ending cash"][-1], start + total, places=6)

    def test_active_customers_recurrence(self):
        s = fm.simulate(self.a)
        st = self.a["revenue_streams"][0]
        new = s["lines"][f"{st['name']}: new customers"]
        act = s["lines"][f"{st['name']}: active customers"]
        self.assertAlmostEqual(act[0], new[0])
        self.assertAlmostEqual(act[5], act[4] * (1 - st["churn"]) + new[5])
        self.assertTrue(all(n <= st["cap"] + 1e-9 for n in new))

    def test_scenarios_ordered(self):
        lo, base, hi = (fm.simulate(fm.apply_scenario(self.a, k))["summary"]["ending_cash"] for k in ("low", "base", "high"))
        self.assertLess(lo, base)
        self.assertLess(base, hi)

    def test_sensitivity_ranked(self):
        rows = fm.sensitivity(self.a)
        swings = [r["swing"] for r in rows]
        self.assertEqual(swings, sorted(swings, reverse=True))

    def test_validation(self):
        bad = json.loads(json.dumps(fm.TEMPLATE))
        bad["revenue_streams"][0]["monthly_churn"] = 2
        with self.assertRaises(ValueError):
            fm.normalise(bad)

    def test_cli_and_spreadsheet_formulas(self):
        out = self.tmp / "fin"
        p = run(str(SCRIPTS / "financial_model.py"), str(SKILL / "examples" / "financial_assumptions.example.json"),
                "--out", str(out), "--sensitivity")
        self.assertEqual(p.returncode, 0, p.stderr)
        for f in ("model.xlsx", "monthly.csv", "summary.md"):
            self.assertTrue((out / f).exists(), f)
        self.assertIn("## Sensitivity", (out / "summary.md").read_text())

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            self.skipTest("LibreOffice not installed; skipped formula recalculation check")
        import openpyxl
        lo = out / "lo"
        subprocess.run([soffice, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(lo),
                        str(out / "model.xlsx")], capture_output=True, timeout=180)
        wb = openpyxl.load_workbook(lo / "model.xlsx", data_only=True)
        M = wb["Model"]
        rows = {M.cell(r, 1).value: r for r in range(1, M.max_row + 1) if M.cell(r, 1).value}
        with open(out / "monthly.csv", encoding="utf-8") as f:
            py = {row[0]: [float(x) for x in row[1:]] for row in csv.reader(f) if row[0] != "Line"}
        for label, vals in py.items():
            self.assertIn(label, rows)
            for i, v in enumerate(vals):
                got = M.cell(rows[label], i + 2).value
                self.assertIsNotNone(got, f"{label} month {i + 1} empty")
                self.assertAlmostEqual(float(got), v, delta=0.02, msg=f"{label} month {i + 1}")
        s = fm.simulate(self.a)["summary"]
        S = wb["Summary"]
        self.assertEqual(S["B4"].value, s["break_even_month"])
        self.assertAlmostEqual(S["B5"].value, s["lowest_cash"], delta=0.01)


class Workspace(unittest.TestCase):
    def test_init_is_idempotent_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d) / "business"
            self.assertEqual(run(str(SCRIPTS / "init_workspace.py"), str(ws)).returncode, 0)
            brief = ws / "00-hq" / "BRIEF.md"
            brief.write_text("founder edits")
            p = run(str(SCRIPTS / "init_workspace.py"), str(ws))
            self.assertIn("Nothing to do", p.stdout)
            self.assertEqual(brief.read_text(), "founder edits")
            self.assertEqual(run(str(SCRIPTS / "init_workspace.py"), "--check", str(ws)).returncode, 0)


class PluginStructure(unittest.TestCase):
    AGENTS = ["biz-market-analyst", "biz-competitor-analyst", "biz-customer-researcher", "biz-strategist",
              "biz-brand-builder", "biz-product-lead", "biz-finance-lead", "biz-legal-advisor",
              "biz-marketing-lead", "biz-sales-lead", "biz-ops-lead", "biz-fundraising-lead", "biz-red-team"]

    def frontmatter(self, path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), path)
        block = text.split("---\n", 2)[1]
        out = {}
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
        return out

    def test_every_agent_exists_and_matches_skill(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in self.AGENTS:
            fmd = self.frontmatter(ROOT / "agents" / f"{name}.md")
            self.assertEqual(fmd["name"], name)
            self.assertTrue(fmd["description"])
            self.assertNotIn("Agent", fmd.get("tools", ""), f"{name} must not spawn subagents")
            self.assertIn(name, skill)

    def test_workspace_folders_match_progress_template(self):
        import init_workspace as iw
        progress = (SKILL / "templates" / "PROGRESS.md").read_text(encoding="utf-8")
        for folder, owner in iw.DEPARTMENTS[1:]:
            self.assertIn(folder, progress)
            self.assertIn(owner, progress)

    def test_skill_description_length(self):
        d = self.frontmatter(SKILL / "SKILL.md")["description"]
        self.assertLessEqual(len(d), 1024)
        self.assertNotIn("<", d)

    def test_manifests_parse(self):
        for f in ("plugin.json", "marketplace.json"):
            json.loads((ROOT / ".claude-plugin" / f).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
