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
import plan_vs_actual as pva  # noqa: E402
import pricing_calc as pc  # noqa: E402
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
        with open(SKILL / "examples" / "financial_assumptions.product.example.json", encoding="utf-8") as f:
            cls.product = fm.normalise(json.load(f))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cash_identity(self):
        for a in (self.a, self.product):
            L = fm.simulate(a)["lines"]
            total = (sum(L["Net profit"]) + sum(L["Funding received"]) - sum(L["Startup costs"])
                     - sum(L["Inventory purchased"]) + sum(L["Inventory used (already paid)"]))
            self.assertAlmostEqual(L["Ending cash"][-1], a["starting_cash"] + total, places=6)

    def test_inventory_balance(self):
        L = fm.simulate(self.product)["lines"]
        bought = sum(L["Inventory purchased"])
        self.assertGreater(bought, 0)
        self.assertTrue(all(x >= -1e-9 for x in L["Inventory on hand"]))
        self.assertTrue(all(u <= c + 1e-9 for u, c in zip(L["Inventory used (already paid)"], L["Cost of goods"])))
        self.assertAlmostEqual(bought - sum(L["Inventory used (already paid)"]), L["Inventory on hand"][-1], places=6)
        # buying stock up front lowers early cash versus the same plan with no stock purchases
        no_stock = dict(self.product, inventory_purchases=[])
        self.assertLess(fm.simulate(self.product)["lines"]["Ending cash"][0],
                        fm.simulate(no_stock)["lines"]["Ending cash"][0])

    def test_stream_start_month(self):
        s = next(x for x in self.product["revenue_streams"] if x["start"] > 1)
        key = f"{s['name']}: " + ("new customers" if s["type"] == "recurring" else "units sold")
        vals = fm.simulate(self.product)["lines"][key]
        self.assertTrue(all(v == 0 for v in vals[: s["start"] - 1]))
        self.assertAlmostEqual(vals[s["start"] - 1], min(s["volume1"], s["cap"] or 1e18))

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

    def check_spreadsheet(self, example: str, assumptions: dict):
        out = self.tmp / example
        p = run(str(SCRIPTS / "financial_model.py"), str(SKILL / "examples" / f"{example}.json"),
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
                self.assertAlmostEqual(float(got), v, delta=0.02, msg=f"{example}: {label} month {i + 1}")
        s = fm.simulate(assumptions)["summary"]
        S = wb["Summary"]
        self.assertEqual(S["B4"].value, s["break_even_month"])
        self.assertAlmostEqual(S["B5"].value, s["lowest_cash"], delta=0.01)

    def test_spreadsheet_formulas_service_example(self):
        self.check_spreadsheet("financial_assumptions.example", self.a)

    def test_spreadsheet_formulas_product_example(self):
        self.check_spreadsheet("financial_assumptions.product.example", self.product)


class PricingCalc(unittest.TestCase):
    def test_product_maths(self):
        r = pc.product({"unit_costs": {"a": 5}, "target_margin_pct": 0.2, "channels": [{
            "name": "site", "price": 20, "units_per_order": 2, "platform_fee_pct": 0.1, "payment_fee_pct": 0.0,
            "payment_fee_fixed": 1, "fulfilment_per_order": 2, "shipping_cost": 8, "shipping_charged": 5,
            "returns_pct": 0.0, "ad_cost_per_order": 6, "fee_source": "test"}]})
        ch = r["channels"][0]
        # revenue 45; fees 4.5 + 1; landed 10; fulfil 2; ship 8 -> before ads 19.5, after ads 13.5
        self.assertAlmostEqual(ch["order_revenue"], 45)
        self.assertAlmostEqual(ch["contribution_before_ads"], 19.5)
        self.assertAlmostEqual(ch["contribution_after_ads"], 13.5)
        self.assertAlmostEqual(ch["kept_per_unit_after_ads"], 6.75)
        self.assertAlmostEqual(ch["break_even_roas"], 45 / 19.5)
        # price for 20% margin: revenue >= (1+10+2+8+6)/(1-0.1-0.2) = 38.571..; price = (38.571-5)/2
        self.assertAlmostEqual(ch["price_for_target_margin"], (27 / 0.7 - 5) / 2)

    def test_losing_channel_flagged(self):
        r = pc.product({"unit_costs": {"a": 10}, "channels": [{"name": "x", "price": 11, "ad_cost_per_order": 5,
                                                                "fee_source": "t"}]})
        self.assertTrue(any("loses money" in f for f in r["channels"][0]["flags"]))

    def test_template_and_service_cli(self):
        p = run(str(SCRIPTS / "pricing_calc.py"), "product", str(SKILL / "examples" / "pricing.product.example.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Most kept per unit", p.stdout)
        p = run(str(SCRIPTS / "pricing_calc.py"), "service", "--target-income", "46000", "--overhead", "0",
                "--billable-hours", "20", "--weeks", "46", "--buffer", "0", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertAlmostEqual(json.loads(p.stdout)["hourly_rate"], 50)


class PlanVsActual(unittest.TestCase):
    def test_flags_two_bad_months(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            run(str(SCRIPTS / "financial_model.py"), str(SKILL / "examples" / "financial_assumptions.example.json"),
                "--out", str(out), "--no-xlsx")
            act = out / "ACTUALS.csv"
            act.write_text("month,revenue,operating_expenses,net_profit,ending_cash,new_customers,notes\n"
                           "1,10,9000,-9000,-500,0,\n2,10,9000,-9000,-900,0,\n")
            r = pva.compare(pva.load_plan(str(out / "monthly.csv")), pva.load_actuals(str(act)), 0.2)
            text = " ".join(r["flags"])
            self.assertIn("revenue has been off plan", text)
            self.assertIn("ending cash is negative", text)
            self.assertTrue(all(x["off_track"] for x in r["rows"] if x["metric"] == "revenue"))

    def test_template(self):
        p = run(str(SCRIPTS / "plan_vs_actual.py"), "--template")
        self.assertTrue(p.stdout.startswith("month,revenue"))
        self.assertEqual(p.stdout, (SKILL / "templates" / "ACTUALS.csv").read_text())


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
              "biz-marketing-lead", "biz-content-lead", "biz-sales-lead", "biz-commerce-lead",
              "biz-retention-lead", "biz-ops-lead", "biz-fundraising-lead", "biz-red-team"]

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
            body = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn("references/playbooks.md", body, f"{name} must read its playbook section")

    def test_agent_folders_match_workspace(self):
        import re
        import init_workspace as iw
        owner_to_folder = {o: f for f, o in iw.DEPARTMENTS}
        for name in self.AGENTS:
            body = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
            folders = re.findall(r"usually `([0-9]+-[a-z]+)/`", body)
            self.assertEqual(folders, [owner_to_folder[name]], name)
        self.assertEqual(sorted(o for _, o in iw.DEPARTMENTS[1:]), sorted(self.AGENTS))

    def test_playbooks_cover_types_and_only_known_departments(self):
        text = (SKILL / "references" / "playbooks.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("\n## "), 16)
        for dept in ("content", "sales", "commerce", "retention", "fundraising"):
            self.assertIn(dept, text)

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
